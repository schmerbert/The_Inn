# forest — woods insert, refuse, traverse (layer 1 gate).
#
# Stores: entries + edges in woods.db
# Refuses: missing signature, orphan inserts, silent rewrite, delete
# Returns: entry id on insert
# Test: tests/hostile/test_invented_fact_open_question.py

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

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


def insert(
    conn: sqlite3.Connection,
    *,
    forest: str,
    bucket: str,
    signature: str,
    authority: str,
    body: str,
    visibility: str = "open",
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
    if bucket == "adoption_record" and not content_hash:
        raise ForestRefusal("adoption_record requires content_hash")

    if not is_pair_root and origin_to_id is None:
        raise ForestRefusal("orphan insert refused: missing origin edge")

    ts = created_at or datetime.now(timezone.utc).isoformat()
    cur = conn.execute(
        """
        INSERT INTO entries (
          created_at, forest, bucket, signature, authority, visibility,
          content_hash, body
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (ts, forest, bucket, signature, authority, visibility, content_hash, body),
    )
    entry_id = int(cur.lastrowid)

    if origin_to_id is not None:
        conn.execute(
            "INSERT INTO edges (from_id, to_id, kind) VALUES (?, ?, ?)",
            (entry_id, origin_to_id, origin_kind),
        )

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
