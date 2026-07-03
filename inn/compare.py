# compare — drawer file vs adoption trail (test 5).
#
# Stores: nothing
# Refuses: missing adoption_record
# Returns: list of warning dicts
# Test: tests/hostile/test_compare_drawer_mismatch.py

from __future__ import annotations

import hashlib
import sqlite3
from pathlib import Path

from inn.errors import InnRefusal
from inn.shelve import content_hash


def file_hash(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def adoption_hash_for_entry(conn: sqlite3.Connection, entry_id: int) -> str | None:
    row = conn.execute(
        "SELECT content_hash, bucket FROM entries WHERE id = ?",
        (entry_id,),
    ).fetchone()
    if row is None:
        return None
    if row["bucket"] != "adoption_record":
        raise InnRefusal(f"entry {entry_id} is not an adoption_record")
    return row["content_hash"]


def check_drawer(
    file_path: Path,
    conn: sqlite3.Connection,
    adoption_entry_id: int,
) -> list[dict]:
    """Return warnings if on-disk file does not match adoption content_hash."""
    warnings: list[dict] = []
    if not file_path.exists():
        warnings.append({
            "label": "warning",
            "text": f"drawer missing: {file_path}",
            "path": str(file_path),
        })
        return warnings

    recorded = adoption_hash_for_entry(conn, adoption_entry_id)
    if recorded is None:
        warnings.append({
            "label": "warning",
            "text": f"no adoption_record for id {adoption_entry_id}",
            "id": adoption_entry_id,
        })
        return warnings

    actual = file_hash(file_path)
    if actual != recorded:
        warnings.append({
            "label": "warning",
            "text": "drawer file does not match adoption trail",
            "path": str(file_path),
            "adoption_entry_id": adoption_entry_id,
            "expected_hash": recorded,
            "actual_hash": actual,
        })
    return warnings
