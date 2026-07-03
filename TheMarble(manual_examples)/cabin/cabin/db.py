"""db.py — the geography.

This module owns the *shape* of .cabin's memory: the connection, the local
vector extension, and the schema. The schema is not incidental — it **is** the
contamination firewall made physical:

  - Every bucket is its own pair of tables (content + vec companion). One
    polluted bucket therefore cannot reach another: they are separate vector
    indexes, not rows sharing one. This is what makes quarantine real (§3.2).
  - The `forest` column ('home' | 'wild') is LAW II as geography: raw history
    lives in 'wild' and can never be dragged into 'home' (the crossing is
    enforced at the one write door, _commit; see forest.py).
  - `enabled` is the circuit-breaker: flip a bucket off and the collector skips
    it. Nothing is deleted; the pollution simply stops surfacing.

THE ONE THING NOT TO DO HERE: never build a table name from raw caller input.
Bucket slugs are interpolated into table names (`forest_<bucket>`), and SQLite
has no parameter binding for identifiers. Every slug therefore passes
`validate_slug` AND must resolve to a registry row before it touches SQL. That
guard lives in `_table_for`. Route every table-name through it.

No migration framework lives here on purpose: there is nothing yet to migrate
*from*. `init_db` is idempotent (CREATE ... IF NOT EXISTS). A real migration
runner arrives the day a schema actually changes — not as speculative bloat.
"""

from __future__ import annotations

import re
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

import sqlite_vec

# Embedding width. all-MiniLM-L6-v2, unit-normalized (see embed.py). The vec0
# companion tables are declared FLOAT[384]; keep this in lockstep with embed.py.
EMBED_DIM = 384

# A bucket slug becomes part of a table name. This is the injection gate: lower
# snake, starts with a letter, <= 32 chars. Anything else never reaches SQL.
BUCKET_SLUG_RE = re.compile(r"^[a-z][a-z0-9_]{0,31}$")


def utcnow() -> str:
    """ISO-8601 UTC timestamp. One spelling of 'now' across the codebase."""
    return datetime.now(timezone.utc).isoformat()


# --------------------------------------------------------------------------- #
# Connection
# --------------------------------------------------------------------------- #

def connect(db_path: str | Path) -> sqlite3.Connection:
    """Open a .cabin store and load the local vector extension.

    The sqlite-vec load sequence is exact (enable, load, disable) — it is the
    only place extension loading is permitted. WAL mode is set so a reader (the
    forest browser, later) can run while the worker writes.
    """
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row

    conn.enable_load_extension(True)
    sqlite_vec.load(conn)
    conn.enable_load_extension(False)

    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


# --------------------------------------------------------------------------- #
# Slugs and table-name resolution (the injection gate)
# --------------------------------------------------------------------------- #

def validate_slug(slug: str) -> str:
    """Return the slug if it is a legal identifier, else raise. Pure check."""
    if not isinstance(slug, str) or not BUCKET_SLUG_RE.match(slug):
        raise ValueError(
            f"illegal bucket slug {slug!r}: must match {BUCKET_SLUG_RE.pattern}"
        )
    return slug


def _table_for(conn: sqlite3.Connection, bucket: str) -> tuple[str, str]:
    """Resolve a bucket to its (content_table, vec_table) literal names.

    Two gates, both mandatory: the slug is regex-valid AND a registry row for it
    exists. The registry — not caller input — is the source of truth for what
    tables may be named. This is the single chokepoint for turning a bucket into
    an SQL identifier; nothing else in the codebase constructs `forest_<x>`.
    """
    validate_slug(bucket)
    row = conn.execute(
        "SELECT bucket FROM forest_registry WHERE bucket = ?", (bucket,)
    ).fetchone()
    if row is None:
        raise ValueError(f"unknown bucket {bucket!r}: not in forest_registry")
    return f"forest_{bucket}", f"vec_{bucket}"


# --------------------------------------------------------------------------- #
# Schema
# --------------------------------------------------------------------------- #

# The registry: one row per bucket. The collector reads this to know what exists
# and what is live. `voiced` records whether a bucket may legally hold authored
# prose (personal, rationale, craft, seedbank) vs. extraction only.
_REGISTRY_DDL = """
CREATE TABLE IF NOT EXISTS forest_registry (
    bucket      TEXT PRIMARY KEY,
    forest      TEXT NOT NULL,          -- 'home' | 'wild'  (LAW II geography)
    enabled     INTEGER NOT NULL DEFAULT 1,   -- the circuit-breaker
    voiced      INTEGER NOT NULL DEFAULT 0,   -- 1 = may hold authored prose
    created_at  TEXT NOT NULL,
    note        TEXT
)
"""

# The raw archive (§17) — the cold Wild layer. Holds the actual ground an
# authored memory points DOWN to (a directive's text, a session exchange):
# append-only and immutable, so a mark's receipt can't be edited out from under
# the claim. It is NOT a registry bucket, has NO vec companion, and is NEVER
# embedded or returned by the collector. It is the earth the trail leads to,
# not a trail you walk. The trail (a Home entry's source ref) leads off to it;
# nothing raw is ever hauled back up onto the trail (that would be LAW II).
_RAW_ARCHIVE_DDL = """
CREATE TABLE IF NOT EXISTS raw_archive (
    id           TEXT PRIMARY KEY,
    project      TEXT,
    source_kind  TEXT NOT NULL,
    content      TEXT NOT NULL,
    content_hash TEXT NOT NULL,
    created_at   TEXT NOT NULL
)
"""

# Shared content-table schema, one physical table PER bucket. The provenance
# columns (writer..model) are the smoke alarm: written once at insert, never
# rewritten, dense enough to trace any infection path AND to re-challenge any
# authored claim. Append-only is enforced at the write door, not by a trigger
# here, so the rule lives next to the code that could break it.
_CONTENT_DDL = """
CREATE TABLE IF NOT EXISTS forest_{bucket} (
    id               TEXT PRIMARY KEY,        -- uuid4
    project          TEXT,                    -- scope key; NULL for global buckets
    source_type      TEXT NOT NULL,           -- provenance label
    source_id        TEXT,                    -- e.g. 'boundary:<wild8>:<lens>'
    body             TEXT NOT NULL,           -- verbatim span OR authored mark (LAW I)
    author           TEXT,                    -- 'cabin' if voiced; 'extract' if voiceless
    embedding        BLOB,                    -- float32 384-dim, mirrors vec table

    -- provenance chain (append-only; never UPDATEd after insert)
    writer           TEXT NOT NULL,           -- 'extract'|'plant'|'synthesize'|'archive'
    source_kind      TEXT,                    -- closed vocab (§5) — makes source-grip enforceable
    source_hash      TEXT,                    -- sha256 of source span at write time (drift detector)
    filter_version   TEXT,                    -- which extraction-filter version touched it
    lesson           TEXT,                    -- lesson label: move principle (plant) or synthesis perspective
    model            TEXT,                    -- which model authored this entry (e.g. 'claude-sonnet-4-6')

    created_at            TEXT NOT NULL,
    traversed_at          TEXT,
    traversal_count       INTEGER NOT NULL DEFAULT 0,
    human_traversal_count INTEGER NOT NULL DEFAULT 0,
    surface_pressure      INTEGER NOT NULL DEFAULT 0,
    neighbor_pressure     INTEGER NOT NULL DEFAULT 0,
    dismissed             INTEGER NOT NULL DEFAULT 0
)
"""

_CONTENT_INDEXES = (
    "CREATE INDEX IF NOT EXISTS idx_{bucket}_project ON forest_{bucket}(project)",
    "CREATE INDEX IF NOT EXISTS idx_{bucket}_type    ON forest_{bucket}(source_type)",
)

# vec0 companion: the per-bucket vector index. Physically separate from every
# other bucket's — that separateness is the whole point (quarantinability).
_VEC_DDL = """
CREATE VIRTUAL TABLE IF NOT EXISTS vec_{bucket} USING vec0(
    entry_id  TEXT PRIMARY KEY,
    embedding FLOAT[{dim}]
)
"""


# Default buckets per scope. A store is either a per-project Home/Wild, or the
# global shed. The taxonomy (which bucket is voiced, which forest it sits in) is
# fixed here so it cannot be set wrong by a caller. (§3.2 table.)
#   (slug, forest, voiced, note)
DEFAULT_BUCKETS: dict[str, tuple[tuple[str, str, int, str], ...]] = {
    "project": (
        ("project",       "home", 0, "extracted working memory of this repo; no authored decisions"),
        ("personal",      "home", 1, "marks: things deliberately chosen to remember"),
        ("rationale",     "home", 1, "authored decisions and recovered why; source-grip required"),
        ("conversations", "wild", 0, "raw chat archive; cold, foragable, never auto-fed (LAW II)"),
        # The concept-index: auto-built from repo symbols each session (§20.4).
        # Voiceless (extraction only), per-project, disposable — these three
        # properties together are what make auto-ingestion of raw code legal here
        # and illegal everywhere else. The bucket is quarantinable like any other.
        ("repo_map",      "home", 0, "concept-index: this repo's symbols; auto-built, nests by time"),
    ),
    "global": (
        ("craft",    "home", 1, "the wood shed: cross-project worker memory"),
        ("seedbank", "home", 1, "patterns/intentions with no ground yet"),
    ),
}


def create_bucket(
    conn: sqlite3.Connection,
    slug: str,
    forest: str,
    voiced: bool,
    note: str = "",
) -> None:
    """Create one bucket: registry row + content table + vec companion + indexes.

    Explicit and validated — never a side effect of a write. Writers reject
    unknown buckets rather than auto-creating them, because auto-create is how a
    typo becomes a permanent ghost table.
    """
    validate_slug(slug)
    if forest not in ("home", "wild"):
        raise ValueError(f"forest must be 'home' or 'wild', got {forest!r}")

    conn.execute(
        "INSERT OR IGNORE INTO forest_registry "
        "(bucket, forest, enabled, voiced, created_at, note) "
        "VALUES (?, ?, 1, ?, ?, ?)",
        (slug, forest, int(bool(voiced)), utcnow(), note),
    )
    conn.execute(_CONTENT_DDL.format(bucket=slug))
    # Idempotent migrations: add columns to existing tables that predate them.
    for _col_ddl in (
        f"ALTER TABLE forest_{slug} ADD COLUMN model TEXT",
        f"ALTER TABLE forest_{slug} ADD COLUMN human_traversal_count INTEGER NOT NULL DEFAULT 0",
    ):
        try:
            conn.execute(_col_ddl)
            conn.commit()
        except Exception:
            pass  # column already present
    for idx in _CONTENT_INDEXES:
        conn.execute(idx.format(bucket=slug))
    conn.execute(_VEC_DDL.format(bucket=slug, dim=EMBED_DIM))
    conn.commit()


def init_db(conn: sqlite3.Connection, scope: str) -> None:
    """Idempotent. Build the registry and this scope's default buckets.

    scope is 'project' (per-repo Home + Wild) or 'global' (the shed). Safe to
    call on every open; CREATE ... IF NOT EXISTS means a built store is left
    untouched.
    """
    if scope not in DEFAULT_BUCKETS:
        raise ValueError(f"scope must be one of {tuple(DEFAULT_BUCKETS)}, got {scope!r}")
    conn.execute(_REGISTRY_DDL)
    if scope == "project":
        # the cold Wild layer (raw_archive) lives with the project's Wild; the
        # global shed has no raw ground to point at.
        conn.execute(_RAW_ARCHIVE_DDL)
    conn.commit()
    for slug, forest, voiced, note in DEFAULT_BUCKETS[scope]:
        create_bucket(conn, slug, forest, bool(voiced), note)


# --------------------------------------------------------------------------- #
# The circuit-breaker
# --------------------------------------------------------------------------- #

def set_enabled(conn: sqlite3.Connection, bucket: str, enabled: bool) -> None:
    """Flip a bucket's circuit-breaker. Quarantine without deletion."""
    _table_for(conn, bucket)  # validates existence
    conn.execute(
        "UPDATE forest_registry SET enabled = ? WHERE bucket = ?",
        (int(bool(enabled)), bucket),
    )
    conn.commit()


def list_buckets(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    """Every registered bucket, for `cabin bucket list` and the collector."""
    return conn.execute(
        "SELECT bucket, forest, enabled, voiced, created_at, note "
        "FROM forest_registry ORDER BY forest, bucket"
    ).fetchall()


def enabled_buckets(conn: sqlite3.Connection, forest: str) -> list[str]:
    """Live bucket slugs in a forest. The collector reads only these."""
    rows = conn.execute(
        "SELECT bucket FROM forest_registry WHERE forest = ? AND enabled = 1 "
        "ORDER BY bucket",
        (forest,),
    ).fetchall()
    return [r["bucket"] for r in rows]
