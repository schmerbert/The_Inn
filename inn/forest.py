# forest — woods insert, refuse, traverse; ceremony primitives.
#
# Stores: entries + edges in woods.db
# Refuses: missing signature, orphan inserts, adoption_record without content_hash, silent rewrite
# Returns: int entry id on insert; connect/init_db paths; search → list[Row]
# Test: tests/hostile/test_invented_fact_open_question.py
#
# TRAILHEAD — forest.adopt() is woods-only. Ground files: inn.shelve.shelve only.
#
# Use (cold worker):
#   connect(), init_db()           — woods.db (inhale calls init_db every wake)
#   insert(), insert_pair_root()   — custody entries
#   insert_pair()                  — helper for real-time message ingest (layer 4)
#   refuse_ground_invention()      — invented fact → question bucket
#   adopt()                        — woods ceremony only — NOT ground markdown

from __future__ import annotations

import hashlib
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from inn.errors import ForestRefusal
from inn.paths import repo_root

PAIR_ROOT_KINDS = frozenset({"spoken_in", "responds_to"})


def db_path(root: Path | None = None) -> Path:
    root = root or repo_root()
    return root / "woods" / "woods.db"


def schema_path(root: Path | None = None) -> Path:
    root = root or repo_root()
    return root / "woods" / "schema.sql"


def connect(root: Path | None = None) -> sqlite3.Connection:
    root = root or repo_root()
    db_path(root).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path(root))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(root: Path | None = None) -> None:
    root = root or repo_root()
    sql = schema_path(root).read_text(encoding="utf-8")
    with connect(root) as conn:
        conn.executescript(sql)
        conn.commit()


def hash_body(body: str) -> str:
    return hashlib.sha256(body.encode("utf-8")).hexdigest()


def add_edge(conn: sqlite3.Connection, from_id: int, to_id: int, kind: str) -> None:
    conn.execute(
        "INSERT OR IGNORE INTO edges (from_id, to_id, kind) VALUES (?, ?, ?)",
        (from_id, to_id, kind),
    )


def insert(
    conn: sqlite3.Connection,
    *,
    forest: str,
    bucket: str,
    signature: str,
    authority: str,
    body: str,
    visibility: str = "open",
    meta: dict[str, Any] | None = None,
    content_hash: str | None = None,
    origin_to_id: int | None = None,
    origin_kind: str = "spoken_in",
    is_pair_root: bool = False,
    created_at: str | None = None,
) -> int:
    if not signature or not str(signature).strip():
        raise ForestRefusal("missing signature")
    if not body or not str(body).strip():
        raise ForestRefusal("empty body")
    if forest not in ("home", "wild"):
        raise ForestRefusal(f"invalid forest: {forest}")
    if not is_pair_root and bucket != "session_pair" and origin_to_id is None:
        raise ForestRefusal("orphan insert refused: missing origin edge")
    if bucket == "adoption_record" and not content_hash:
        raise ForestRefusal("adoption_record requires content_hash (room file at Shelving)")

    ts = created_at or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%fZ")
    cur = conn.execute(
        """
        INSERT INTO entries (
          created_at, forest, bucket, signature, authority, visibility,
          body, body_hash, content_hash, meta_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            ts,
            forest,
            bucket,
            signature,
            authority,
            visibility,
            body,
            hash_body(body),
            content_hash,
            json.dumps(meta or {}, sort_keys=True),
        ),
    )
    entry_id = int(cur.lastrowid)

    if origin_to_id is not None:
        add_edge(conn, entry_id, origin_to_id, origin_kind)

    return entry_id


def insert_pair_root(
    conn: sqlite3.Connection,
    *,
    signature: str,
    body: str,
    bucket: str = "session_pair",
) -> int:
    return insert(
        conn,
        forest="home",
        bucket=bucket,
        signature=signature,
        authority="model",
        body=body,
        is_pair_root=True,
    )


def insert_pair(
    conn: sqlite3.Connection,
    *,
    guest_words: str,
    innkeeper_words: str | None = None,
    guest_signature: str = "guest",
    innkeeper_signature: str = "model",
) -> tuple[int, int | None]:
    """Insert one conversational pair in real time (layer 4 trailhead).

    Returns `(pair_root_id, response_id_or_none)`.
    """
    pair_root_id = insert(
        conn,
        forest="home",
        bucket="session_pair",
        signature=guest_signature,
        authority="stranger",
        body=guest_words,
        is_pair_root=True,
    )

    response_id: int | None = None
    if innkeeper_words is not None and innkeeper_words.strip():
        response_id = insert(
            conn,
            forest="home",
            bucket="session_pair",
            signature=innkeeper_signature,
            authority="model",
            body=innkeeper_words,
            origin_to_id=pair_root_id,
            origin_kind="responds_to",
        )

    return pair_root_id, response_id


def open_question(
    conn: sqlite3.Connection,
    *,
    question: str,
    signature: str,
    origin_to_id: int,
) -> int:
    """Invented or unknown facts land here — not canon."""
    return insert(
        conn,
        forest="home",
        bucket="question",
        signature=signature,
        authority="model",
        body=question,
        origin_to_id=origin_to_id,
        origin_kind="spoken_in",
    )


def refuse_ground_invention(conn: sqlite3.Connection, *, detail: str, pair_root_id: int) -> int:
    """Hostile test 3 path: do not write canon; record open question."""
    return open_question(
        conn,
        question=f"OPEN: {detail}",
        signature="model",
        origin_to_id=pair_root_id,
    )


def adopt(
    conn: sqlite3.Connection,
    *,
    adopted_entry_id: int,
    quote: str,
    content_hash: str,
    new_ground_body: str | None = None,
) -> int:
    """Woods-only adoption ceremony — NOT the marble Shelving crossing.

    Does not write markdown ground files. Hosts and models must use shelve.py.
    """
    record_id = insert(
        conn,
        forest="home",
        bucket="adoption_record",
        signature="author",
        authority="record",
        body=quote,
        content_hash=content_hash,
        origin_to_id=adopted_entry_id,
        origin_kind="adopts",
    )
    if new_ground_body:
        insert(
            conn,
            forest="home",
            bucket="canon",
            signature="author",
            authority="ground",
            body=new_ground_body,
            origin_to_id=record_id,
            origin_kind="derived_from",
        )
    return record_id


def supersede(
    conn: sqlite3.Connection,
    *,
    old_id: int,
    new_body: str,
    signature: str = "author",
) -> int:
    with conn:
        new_id = insert(
            conn,
            forest="home",
            bucket="canon",
            signature=signature,
            authority="ground",
            body=new_body,
            origin_to_id=old_id,
            origin_kind="supersedes",
        )
        conn.execute(
            "UPDATE entries SET superseded_by = ? WHERE id = ?",
            (new_id, old_id),
        )
        conn.execute(
            "UPDATE entries SET bucket = 'superseded_canon' WHERE id = ? AND bucket = 'canon'",
            (old_id,),
        )
    return new_id


def search(
    conn: sqlite3.Connection,
    query: str,
    *,
    open_buckets: Iterable[str] | None = None,
) -> list[sqlite3.Row]:
    buckets = list(open_buckets or [])
    conn.execute(
        "INSERT INTO retrieval_log (query, open_buckets_json) VALUES (?, ?)",
        (query, json.dumps(buckets)),
    )
    params: list[object] = [query]
    bucket_clause = ""
    if buckets:
        placeholders = ",".join("?" for _ in buckets)
        bucket_clause = f"AND e.bucket IN ({placeholders})"
        params.extend(buckets)
    return list(
        conn.execute(
            f"""
            SELECT e.*
            FROM entries_fts f
            JOIN entries e ON e.id = f.rowid
            WHERE entries_fts MATCH ?
              AND e.visibility != 'sealed'
              {bucket_clause}
            ORDER BY rank
            """,
            params,
        )
    )
