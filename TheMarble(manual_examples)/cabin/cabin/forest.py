"""forest.py — the one write door, and the read.

Every byte that becomes memory passes through a single function: `_commit`. The
two LAWS are enforced there, once, in plain sequence — not scattered across the
writers, because duplicated guards drift and a proven prior implementation lost
real data to exactly that drift (two copies of an ingestion cleaner diverged and
contamination leaked through the gap). One door means the hostile suite guards
one surface, and no future writer can bypass the laws by accident.

The four public writers (`extract`, `plant`, `synthesize`, `archive_conversation`)
are thin: each assembles an entry and hands it to `_commit`. They are the only
functions permitted to insert into a forest table. `_commit` is *customs* — it
does no routing, no synthesis, no model call; it validates and inserts, nothing
clever. Synthesis and any judgment happen in the writers, before customs.

THE ONE THING NOT TO DO HERE: do not add a second insert path. If you write a new
way into a forest table that does not go through `_commit`, you have removed the
firewall. There is one door. Keep it the only one.

Law map (read `_commit` top to bottom and you have read the contamination model):
  LAW I  — Extract, never summarize: only verbatim spans (voiceless) or authored,
           attributed prose (voiced) may be stored. Anonymous voiced prose — the
           narrator — is refused at the door.
  LAW II — Wild→Home only by synthesis: raw history lives in 'wild' forever; the
           only thing that crosses to 'home' is an authored, grounded insight.
"""

from __future__ import annotations

import hashlib
import sqlite3
import uuid
from datetime import datetime, timezone
from dataclasses import dataclass, field

import numpy as np

from . import db, embed, instruments
from .filter import FILTER_VERSION, is_pure_scaffolding, strip_scaffolding

# The closed writer vocabulary. A writer not in this set never reaches an insert.
WRITERS = ("extract", "plant", "synthesize", "archive")

# Authored memory must bottom out in *resolvable* ground: the door walks the
# trail itself (`_resolve_source`) and refuses one that leads nowhere. These are
# the writers whose source must resolve, and whose hash is taken over the
# resolved material, never a label. (extract's file_span resolution joins this
# at the extract wiring; archive records raw chat and is not an authored claim.)
_RESOLVE_REQUIRED = ("plant", "synthesize")

# The closed source-kind vocabulary (§5). "Resolvable source" must be a fixed
# enum, not vibes — `_commit` validates the per-writer requirement against this.
SOURCE_KINDS = (
    "file_span",                 # a verbatim span from a repo file
    "wild_entry",                # a forest_<wild bucket> entry id
    "raw_archive_ref",           # a pointer into the append-only raw archive
    "current_session_exchange",  # a turn from the live session
    "user_directive",            # an explicit instruction from the human
    "move_instance",             # a concrete code instance grounding a move
    "manual_note_source",        # a human note (low-priority)
)

# Dedup: a new write within this cosine of an existing entry in the same bucket
# is a near-duplicate and is dropped rather than bloating the bucket.
DEDUP_COSINE = 0.90


class LawViolation(ValueError):
    """Raised when a write would break a LAW. Caught by the hostile suite as the
    proof that the floor refuses illegal memory. The message names the law."""


@dataclass
class Entry:
    """What a writer hands to customs. The provenance fields are the smoke alarm:
    written once, never rewritten, dense enough to trace any infection path and
    to re-challenge any authored claim later."""
    bucket: str
    project: str | None
    source_type: str
    body: str                    # what gets stored (verbatim span or authored prose)
    writer: str
    voiced: bool                 # True = authored prose; False = extraction
    author: str | None = None    # attribution; required iff voiced
    source_id: str | None = None
    source_kind: str | None = None
    source_text: str | None = None  # the material the source_hash is taken over
    lesson: str | None = None
    model: str | None = None     # which model authored this (e.g. 'claude-sonnet-4-6')
    filtered: bool = False       # did the extraction filter touch the body?
    _meta: dict = field(default_factory=dict)


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _wild_entry(conn: sqlite3.Connection, entry_id: str) -> tuple[str, str] | None:
    """Find a raw entry in any enabled 'wild' bucket. Returns (bucket, body) or
    None. This is how `_commit` proves a Wild→Home crossing has a real origin —
    LAW II cannot be satisfied by a source id that points at nothing."""
    for bucket in db.enabled_buckets(conn, "wild"):
        content, _ = db._table_for(conn, bucket)
        row = conn.execute(
            f"SELECT body FROM {content} WHERE id = ?", (entry_id,)
        ).fetchone()
        if row is not None:
            return bucket, row["body"]
    return None


# The raw-archive source kinds resolve against the cold Wild layer (raw_archive),
# never against a forest bucket. `wild_entry` resolves via _wild_entry above;
# `file_span` resolution (reading the file, drift detection) arrives with the
# extract wiring — it is the one mutable ground.
# `move_instance` archives the concrete before→after that grounds a lesson; the
# file reference itself is embedded in that content, not tracked separately.
RAW_ARCHIVE_KINDS = (
    "user_directive", "current_session_exchange", "raw_archive_ref",
    "manual_note_source", "move_instance",
)


def archive_source(conn, project, content, source_kind="user_directive") -> str:
    """Record raw ground in the cold Wild layer and return its ref.

    Append-only: the receipt an authored memory points DOWN to, immutable so it
    cannot be edited out from under the claim. Never embedded, never collected —
    it is the earth the trail leads to, not a trail you walk. Returns the
    raw_archive_ref (a uuid) the memory will carry as its source_id."""
    if source_kind not in SOURCE_KINDS:
        raise LawViolation(f"unknown source_kind {source_kind!r}")
    ref = str(uuid.uuid4())
    conn.execute(
        "INSERT INTO raw_archive "
        "(id, project, source_kind, content, content_hash, created_at) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (ref, project, source_kind, content, _sha256(content), db.utcnow()),
    )
    conn.commit()
    return ref


def _resolve_source(conn, project, source_kind, source_id):
    """Walk an authored memory's trail down to its ground.

    Returns (resolved: bool, material: str | None, mutable: bool). `material` is
    what `_commit` hashes — so the hash is taken over real resolved ground, never
    a label. A trail that leads nowhere returns (False, None, _), and the door
    refuses the write.

      wild_entry        -> the Wild entry body; immutable (a receipt).
      raw-archive kind  -> the raw_archive record's content; immutable (receipt).
      file_span         -> (handled at the extract wiring; the one MUTABLE
                           ground, where a hash mismatch means real drift).
    """
    if source_kind == "wild_entry":
        hit = _wild_entry(conn, source_id)
        return (hit is not None, hit[1] if hit else None, False)
    if source_kind in RAW_ARCHIVE_KINDS:
        row = conn.execute(
            "SELECT content FROM raw_archive WHERE id = ? AND project = ?",
            (source_id, project),
        ).fetchone()
        return (row is not None, row["content"] if row else None, False)
    return (False, None, False)


def _nearest_cosine(conn: sqlite3.Connection, bucket: str, qvec: np.ndarray) -> float:
    """Cosine of the single nearest neighbor in `bucket` (or -1.0 if empty).
    Used for dedup. We rank by the vec index, then compute cosine on the stored
    embedding blob so the threshold is a true cosine, not a distance proxy."""
    content, vec = db._table_for(conn, bucket)
    hit = conn.execute(
        f"SELECT entry_id FROM {vec} WHERE embedding MATCH ? AND k = 1",
        (embed.serialize(qvec),),
    ).fetchone()
    if hit is None:
        return -1.0
    row = conn.execute(
        f"SELECT embedding FROM {content} WHERE id = ?", (hit["entry_id"],)
    ).fetchone()
    if row is None or row["embedding"] is None:
        return -1.0
    other = np.frombuffer(row["embedding"], dtype="<f4")
    return embed.cosine(qvec, other)


# --------------------------------------------------------------------------- #
# The one door
# --------------------------------------------------------------------------- #

def _commit(conn: sqlite3.Connection, entry: Entry) -> dict:
    """Customs. Validate against both LAWS, then insert. Steps 1-6 are pure
    validation and raise before any side effect; 7-12 are the write. The order
    is the contamination model, read top to bottom."""

    # 1. resolve bucket → its tables. Also gate 2 (slug regex) and 3 (registry
    #    row exists): _table_for raises if the slug is illegal or unregistered.
    content_table, vec_table = db._table_for(conn, entry.bucket)
    reg = conn.execute(
        "SELECT forest, voiced FROM forest_registry WHERE bucket = ?",
        (entry.bucket,),
    ).fetchone()
    bucket_forest = reg["forest"]
    bucket_voiced = bool(reg["voiced"])

    # 3. writer must be a known writer.
    if entry.writer not in WRITERS:
        raise LawViolation(f"unknown writer {entry.writer!r}")

    # 4. LAW II — the Wild→Home crossing.
    #    (a) Raw chat (writer 'archive') is Wild-only. It may never target Home —
    #        Home is earned by hand, never bulk-filled.
    if entry.writer == "archive" and bucket_forest != "wild":
        raise LawViolation(
            "LAW II: raw conversation may only enter a 'wild' bucket, "
            f"not '{entry.bucket}' (forest={bucket_forest})"
        )
    #    (b) Anything sourced from a raw Wild entry may cross into Home only as an
    #        authored synthesis — never dragged across raw.
    if bucket_forest == "home" and entry.source_kind == "wild_entry":
        if entry.writer != "synthesize" or not entry.voiced or not entry.author:
            raise LawViolation(
                "LAW II: a Wild entry can reach Home only via attributed "
                "synthesis (authored insight), never as raw material"
            )

    # 5. LAW I — voiced/voiceless. Voiced prose must wear a name AND land in a
    #    bucket licensed for voice. Anonymous voiced prose is the narrator: the
    #    one forbidden cell. Refuse it here, at the door, not in six places.
    if entry.voiced:
        if not entry.author:
            raise LawViolation(
                "LAW I: voiced (authored) prose requires an author — "
                "anonymous voiced memory is the forbidden narrator"
            )
        if not bucket_voiced:
            raise LawViolation(
                f"LAW I: bucket '{entry.bucket}' is voiceless; it may hold only "
                "extracted spans, not authored prose"
            )
    else:
        # Voiceless writes are extraction: stamped 'extract', never a real name.
        entry.author = "extract"

    # 6. source-grip (shape). "Resolvable source" is a closed vocabulary + a
    #    per-writer requirement, so grounding is enforceable, not a matter of
    #    trust. This checks the source's *shape* (kind in vocab, ref present).
    if entry.source_kind is not None and entry.source_kind not in SOURCE_KINDS:
        raise LawViolation(f"unknown source_kind {entry.source_kind!r}")
    _check_source_grip(conn, entry)

    # 6b. source-grip (resolution). For authored memory the door walks the trail
    #     down to its ground and refuses one that leads nowhere — a signature is
    #     not enough; the claim must be challengeable against real ground. The
    #     resolved material (never a label) is what gets hashed in step 8.
    resolved_material = None
    if entry.writer in _RESOLVE_REQUIRED:
        ok, material, _mutable = _resolve_source(
            conn, entry.project, entry.source_kind, entry.source_id)
        if not ok:
            raise LawViolation(
                f"{entry.writer} source {entry.source_id!r} "
                f"({entry.source_kind}) resolves to no ground — an unresolvable "
                "claim is fabrication; the trail must lead somewhere"
            )
        resolved_material = material

    # --- nothing above this line has touched disk ---

    # 7. filter the body if this writer ingests raw material (only 'archive').
    body = entry.body
    filter_version = None
    if entry.filtered:
        body = strip_scaffolding(entry.body, mode="forest")
        filter_version = FILTER_VERSION

    # 8. source_hash over the source MATERIAL — never a label. For mark and
    #    synthesize the door resolved the real ground in 6b (a directive's text,
    #    the Wild-entry body); for extract the body IS the span; for archive it
    #    is the exchange text. The hash lets an authored claim be re-challenged
    #    against its ground. (For *mutable* ground — file_span, at the extract
    #    wiring — a later mismatch means real drift; for immutable raw-archive
    #    and wild records it is the receipt that proves the ground unchanged.)
    if resolved_material is not None:
        source_text = resolved_material
    else:
        source_text = entry.source_text if entry.source_text is not None else body
    source_hash = _sha256(source_text)

    # 9. embed once.
    vector = embed.embed(body)

    # dedup: a near-identical neighbor already present → don't bloat the bucket.
    if _nearest_cosine(conn, entry.bucket, vector) >= DEDUP_COSINE:
        return {"status": "duplicate", "bucket": entry.bucket}

    # 10/11. dual write: content row + vec row, in one transaction.
    entry_id = str(uuid.uuid4())
    now = db.utcnow()
    blob = embed.serialize(vector)
    conn.execute(
        f"INSERT INTO {content_table} "
        "(id, project, source_type, source_id, body, author, embedding, "
        " writer, source_kind, source_hash, filter_version, lesson, model, created_at) "
        "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (entry_id, entry.project, entry.source_type, entry.source_id, body,
         entry.author, blob, entry.writer, entry.source_kind, source_hash,
         filter_version, entry.lesson, entry.model, now),
    )
    conn.execute(
        f"INSERT INTO {vec_table} (entry_id, embedding) VALUES (?, ?)",
        (entry_id, blob),
    )
    conn.commit()  # 12

    return {
        "status": "stored", "id": entry_id, "bucket": entry.bucket,
        "writer": entry.writer, "author": entry.author, "model": entry.model,
        "source_hash": source_hash, "filter_version": filter_version,
    }


def _check_source_grip(conn: sqlite3.Connection, entry: Entry) -> None:
    """Per-writer source requirements (§5). Each writer must bottom out in real,
    nameable ground, or it is not memory — it is opinion wearing a hard hat."""
    if entry.writer == "extract":
        # verbatim span: needs a source_kind and (via _commit) a hash of itself.
        if not entry.source_kind:
            raise LawViolation("extract requires a source_kind (e.g. file_span)")

    elif entry.writer == "plant":
        # voiced plant (shape): a source ref must be present. Its *resolution*
        # to real ground is enforced by the door at 6b — a plant whose ref leads
        # nowhere is refused there. (Bench-only ungrounded notes are out of scope
        # for the floor; every plant here is Home memory-ground.)
        if not entry.source_id:
            raise LawViolation(
                "plant requires ground — an ungrounded plant is the narrator; "
                "put it on the bench, not in Home"
            )

    elif entry.writer == "synthesize":
        # the Wild→Home gate (shape): the source must name a Wild entry. Its
        # resolution to a real Wild entry is enforced by the door at 6b.
        if entry.source_kind != "wild_entry" or not entry.source_id:
            raise LawViolation("synthesize requires a wild_entry source")

    elif entry.writer == "archive":
        if not entry.source_id:
            raise LawViolation("archive requires a source_id (conversation:seq)")

    # Lesson-grounding (moves, §20.3). On a `plant`, `lesson` is the outer doll
    # of a move — the transferable principle that outlives the code it was learned
    # from. It must bottom out in a concrete before→after (move_instance). Any
    # other source_kind is an ungrounded opinion: the narrator wearing a hard hat.
    # Note: `synthesize` also carries a `lesson` field but as a categorization
    # label for the synthesis perspective, not a move principle — rule is plant-only.
    if entry.writer == "plant" and entry.lesson and entry.source_kind != "move_instance":
        raise LawViolation(
            "a lesson must be grounded in a move_instance — "
            "a principle with no concrete before→after is ungrounded opinion"
        )


# --------------------------------------------------------------------------- #
# The four writers — the only ways in. Each maps to a cell of the voice taxonomy.
# --------------------------------------------------------------------------- #

def extract(conn, bucket, project, source_type, source_id, span,
            model: str | None = None) -> dict:
    """VOICELESS + STORED. A verbatim span, chosen not narrated. The safe default.
    Nothing is authored; the body IS the source, so its hash is the span's."""
    return _commit(conn, Entry(
        bucket=bucket, project=project, source_type=source_type,
        source_id=source_id, body=span, writer="extract", voiced=False,
        source_kind="file_span", source_text=span, model=model,
    ))


def plant(conn, bucket, project, body, source_content=None, source_ref=None,
          source_kind="user_directive", lesson: str | None = None,
          model: str | None = None) -> dict:
    """VOICED + STORED + ATTRIBUTED. A deliberate plant, author='cabin'.

    The `body` is the legible surface that goes in the forest (Home) — short and
    sufficient on its own. Its ground is a trail down to the cold Wild layer;
    ground it one of two ways:
      - `source_content`: the raw ground itself — archived to raw_archive, and
        the plant points at (and is hashed over) the new record;
      - `source_ref`: an existing raw_archive ref (or a Wild entry id) to point
        at — pass `source_kind='wild_entry'` for the latter.
    Neither → refused: an ungrounded plant is the narrator. The door re-resolves
    the ref (6b), so the grip is *resolvable*, not merely labelled.

    `lesson` promotes a plant into a move (§20.3): the body becomes the
    transferable principle (outer doll) and source_content carries the concrete
    before→after that earned it. A lesson must be grounded in
    source_kind='move_instance' — enforced at the door by _check_source_grip."""
    if source_content is None and source_ref is None:
        raise LawViolation(
            "plant requires ground — pass source_content (archived) or a "
            "source_ref; an ungrounded plant is the narrator"
        )
    if source_ref is None:
        source_ref = archive_source(conn, project, source_content, source_kind)
    return _commit(conn, Entry(
        bucket=bucket, project=project, source_type="plant", body=body,
        writer="plant", voiced=True, author="cabin", source_id=source_ref,
        source_kind=source_kind, lesson=lesson, model=model,
    ))


def synthesize(conn, project, wild_entry_id, insight, bucket="rationale", lesson="",
               model: str | None = None) -> dict:
    """The Wild→Home gate (LAW II). The raw Wild entry stays where it is; an
    authored insight crosses into Home, signed, and hashed against the Wild
    source (resolved at the door, 6b) so it can be re-challenged. The act of
    synthesis IS the crossing."""
    return _commit(conn, Entry(
        bucket=bucket, project=project, source_type="synthesis", body=insight,
        writer="synthesize", voiced=True, author="cabin",
        source_id=wild_entry_id, source_kind="wild_entry", lesson=lesson or None,
        model=model,
    ))


def archive_conversation(conn, project, conversation_id, exchanges, raw_dir=None,
                         model: str | None = None) -> dict:
    """Raw chat → the Wild 'conversations' bucket, one entry per exchange. Each is
    filtered first; a pure-scaffolding exchange is dropped. Forced to 'wild':
    conversations are Wild-only, always, so Home cannot fill with raw chatter.

    `exchanges` is a list of {'seq': int, 'text': str}.
    `raw_dir`   is an optional Path to write a verbatim JSONL backup before
                filtering — the cold archive that loses nothing (§17)."""
    if raw_dir is not None:
        instruments.archive_session_raw(conversation_id, exchanges, raw_dir)

    stored, skipped, duplicate = [], 0, 0
    for ex in exchanges:
        text = ex.get("text", "")
        if is_pure_scaffolding(text):
            skipped += 1
            continue
        result = _commit(conn, Entry(
            bucket="conversations", project=project, source_type="conversation",
            body=text, writer="archive", voiced=False,
            source_id=f"{conversation_id}:{ex.get('seq')}",
            source_kind="current_session_exchange", source_text=text,
            filtered=True, model=model,
        ))
        if result["status"] == "stored":
            stored.append(result["id"])
        elif result["status"] == "duplicate":
            duplicate += 1
    return {"status": "archived", "stored": len(stored), "skipped": skipped,
            "duplicate": duplicate, "ids": stored}


# --------------------------------------------------------------------------- #
# The collector — read across enabled buckets
# --------------------------------------------------------------------------- #

def collect(conn, query, forest="home", project=None, buckets=None, k=10) -> list[dict]:
    """Forage. Embed the query once, k-NN every ENABLED bucket of `forest`, merge
    by distance, return the top k.

    The circuit-breaker lives here: a disabled bucket is simply absent from the
    search (it is not in `enabled_buckets`), so a quarantined table cannot
    surface and — because each bucket is a physically separate vec index — cannot
    reach the others. That isolation is the whole reason for the table-per-bucket
    schema.

    `buckets` may restrict the search, but only to buckets that are both in
    `forest` and enabled; anything else is ignored (you cannot read a quarantined
    bucket by naming it explicitly)."""
    live = db.enabled_buckets(conn, forest)
    if buckets is not None:
        wanted = set(buckets)
        live = [b for b in live if b in wanted]

    if not live:
        return []

    qvec = embed.embed(query)
    qblob = embed.serialize(qvec)
    # Over-fetch per bucket when we will post-filter by project, then trim — a
    # project filter can drop arbitrarily many of the raw nearest, so ask for
    # more than k to avoid starving the result.
    per_bucket = k * 3 if project is not None else k

    hits: list[dict] = []
    for bucket in live:
        content, vec = db._table_for(conn, bucket)
        rows = conn.execute(
            f"SELECT v.entry_id, v.distance, c.body, c.project, c.source_type, "
            f"       c.author, c.source_id, c.model, c.created_at "
            f"FROM {vec} v JOIN {content} c ON c.id = v.entry_id "
            f"WHERE v.embedding MATCH ? AND k = ? AND c.dismissed = 0 "
            f"ORDER BY v.distance",
            (qblob, per_bucket),
        ).fetchall()
        for r in rows:
            if project is not None and r["project"] != project:
                continue
            hits.append({
                "id": r["entry_id"], "bucket": bucket, "distance": r["distance"],
                "body": r["body"], "project": r["project"],
                "source_type": r["source_type"], "author": r["author"],
                "source_id": r["source_id"], "model": r["model"],
                "created_at": r["created_at"],
            })

    hits.sort(key=lambda h: h["distance"])
    return hits[:k]


_ALL_BUCKETS = ("personal", "project", "rationale", "conversations", "repo_map")
_WINDOW = 6  # entries either side of the start entry in a session trail


def traverse(conn: sqlite3.Connection, entry_id: str, project: str,
             depth: int = 1, human: bool = False) -> dict:
    """Walk the forest from a starting entry.

    Two trail types:
      session  — conversation entries carry source_id = '{session_id}:{line}'.
                 Returns the session trailhead (compaction summary at line 1)
                 and a window of _WINDOW entries either side of the start.
      source   — plant/mark/synthesize entries carry source_id that resolves to
                 raw_archive. Returns the full source content.

    human=True increments human_traversal_count (panel browse) instead of
    traversal_count (model follow). Keeps the two attention signals separate.
    """
    entry_row = None
    entry_bucket = None
    for bucket in _ALL_BUCKETS:
        row = conn.execute(
            f"SELECT id, source_type, source_id, source_kind, body, author, "
            f"       created_at, traversal_count, human_traversal_count "
            f"FROM forest_{bucket} WHERE id = ? AND project = ?",
            (entry_id, project),
        ).fetchone()
        if row:
            entry_row = row
            entry_bucket = bucket
            break

    if entry_row is None:
        return {"error": f"entry {entry_id} not found in project {project}"}

    now = datetime.now(timezone.utc).isoformat()
    if human:
        new_human = (entry_row["human_traversal_count"] or 0) + 1
        conn.execute(
            f"UPDATE forest_{entry_bucket} "
            f"SET traversed_at = ?, human_traversal_count = ? WHERE id = ?",
            (now, new_human, entry_id),
        )
        new_count = entry_row["traversal_count"] or 0
    else:
        new_count = (entry_row["traversal_count"] or 0) + 1
        conn.execute(
            f"UPDATE forest_{entry_bucket} "
            f"SET traversed_at = ?, traversal_count = ? WHERE id = ?",
            (now, new_count, entry_id),
        )
        new_human = entry_row["human_traversal_count"] or 0
    conn.commit()

    entry = {
        "id": entry_row["id"],
        "bucket": entry_bucket,
        "source_type": entry_row["source_type"],
        "source_id": entry_row["source_id"],
        "body": entry_row["body"],
        "author": entry_row["author"],
        "created_at": entry_row["created_at"],
        "traversal_count": new_count,
        "human_traversal_count": new_human,
    }

    source_id = entry_row["source_id"] or ""
    result: dict = {"entry": entry, "depth": depth}

    if entry_bucket == "conversations" and ":" in source_id:
        session_id, line_str = source_id.rsplit(":", 1)
        start_line = int(line_str)

        def _line(sid: str) -> int:
            return int(sid.rsplit(":", 1)[1])

        # Trailhead — lowest line in session (compaction summary)
        th = conn.execute(
            "SELECT id, body, source_id FROM forest_conversations "
            "WHERE source_id LIKE ? AND project = ? "
            "ORDER BY CAST(SUBSTR(source_id, INSTR(source_id,':')+1) AS INTEGER) LIMIT 1",
            (f"{session_id}:%", project),
        ).fetchone()

        # Window around starting entry
        lo, hi = max(1, start_line - _WINDOW), start_line + _WINDOW
        window = conn.execute(
            "SELECT id, body, source_id FROM forest_conversations "
            "WHERE source_id LIKE ? AND project = ? "
            "  AND CAST(SUBSTR(source_id, INSTR(source_id,':')+1) AS INTEGER) BETWEEN ? AND ? "
            "ORDER BY CAST(SUBSTR(source_id, INSTR(source_id,':')+1) AS INTEGER)",
            (f"{session_id}:%", project, lo, hi),
        ).fetchall()

        total = conn.execute(
            "SELECT COUNT(*) FROM forest_conversations "
            "WHERE source_id LIKE ? AND project = ?",
            (f"{session_id}:%", project),
        ).fetchone()[0]

        result["trail_type"] = "session"
        result["session_id"] = session_id
        result["total_in_session"] = total
        result["trailhead"] = (
            {"id": th["id"], "body": th["body"][:400], "source_id": th["source_id"]}
            if th else None
        )
        result["window"] = [
            {"id": r["id"], "body": r["body"][:300], "line": _line(r["source_id"])}
            for r in window
        ]

    elif source_id:
        raw = conn.execute(
            "SELECT id, source_kind, content, created_at FROM raw_archive "
            "WHERE id = ? AND project = ?",
            (source_id, project),
        ).fetchone()
        result["trail_type"] = "source"
        result["source"] = (
            {"id": raw["id"], "source_kind": raw["source_kind"],
             "content": raw["content"], "created_at": raw["created_at"]}
            if raw else {"error": f"source {source_id} not in raw_archive"}
        )

    else:
        result["trail_type"] = "none"

    return result
