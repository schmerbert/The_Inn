# compare — drawer drift, contradictions, adoption trail.
#
# Stores: nothing
# Refuses: missing or wrong-bucket adoption_record (raises InnRefusal)
# Returns: list[dict] warnings — each has at least label + text
# Test: tests/hostile/test_compare_drawer_mismatch.py, test_contradiction.py
#
# Use (cold worker):
#   scan_ground_warnings(root, conn) — inhale packet warnings slot (drift + contradictions)
#   check_drawer(path, conn, adoption_id) — single drawer vs one adoption_record
#   list_adoptions_for_ground_path(conn, path) — full Shelving chain on a drawer
#   latest_adoption_for_ground_path(conn, path) — drift trailhead only (newest id)
# Alias: scan_ground_drawers = scan_drawer_drift (drift only, not contradictions)

from __future__ import annotations

import re
import sqlite3
from pathlib import Path

from inn.errors import InnRefusal
from inn.forest import hash_body
from inn.rooms import list_rooms

# TRAILHEAD — drift checks use the latest adoption_record per ground_path only.
# Older records remain in the chain (see list_adoptions_for_ground_path); each
# snapshots the file at its crossing. Re-shelving appends and adds a new snapshot.

_TOKEN_RE = re.compile(r"[a-z]{4,}")
_MIN_SHARED_WITHIN_ROOM = 2
_MIN_SHARED_CROSS_ROOM = 2


def file_hash(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    return hash_body(text)


def adoption_file_hash_for_entry(conn: sqlite3.Connection, entry_id: int) -> str | None:
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

    recorded = adoption_file_hash_for_entry(conn, adoption_entry_id)
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


def list_adoptions_for_ground_path(
    conn: sqlite3.Connection,
    ground_path: str,
) -> list[int]:
    """All adoption_record ids for a drawer, oldest first — full Shelving chain."""
    rows = conn.execute(
        """
        SELECT id FROM entries
        WHERE bucket = 'adoption_record'
          AND json_extract(meta_json, '$.ground_path') = ?
        ORDER BY id ASC
        """,
        (ground_path,),
    ).fetchall()
    return [int(row["id"]) for row in rows]


def latest_adoption_for_ground_path(
    conn: sqlite3.Connection,
    ground_path: str,
) -> int | None:
    """Newest adoption_record for drift check — trailhead snapshot only."""
    chain = list_adoptions_for_ground_path(conn, ground_path)
    return chain[-1] if chain else None


def _paragraphs(path: Path) -> list[str]:
    if not path.exists():
        return []
    text = path.read_text(encoding="utf-8").strip()
    if not text:
        return []
    return [part.strip() for part in text.split("\n\n") if part.strip()]


def _significant_tokens(text: str) -> set[str]:
    return set(_TOKEN_RE.findall(text.lower()))


def _paragraph_contradictions(paragraphs: list[str], *, path: str) -> list[dict]:
    """Same drawer: paragraphs share subject tokens but disagree in full text."""
    warnings: list[dict] = []
    for i, first in enumerate(paragraphs):
        first_tokens = _significant_tokens(first)
        for second in paragraphs[i + 1 :]:
            shared = first_tokens & _significant_tokens(second)
            if len(shared) >= _MIN_SHARED_WITHIN_ROOM and first != second:
                warnings.append({
                    "label": "warning",
                    "text": "possible contradiction between ground paragraphs",
                    "path": path,
                    "shared_terms": sorted(shared),
                })
    return warnings


def _cross_room_contradictions(
    study_paragraphs: list[str],
    manuscript_paragraphs: list[str],
) -> list[dict]:
    """Study canon vs manuscript ground — overlapping subject, differing text."""
    warnings: list[dict] = []
    for study_para in study_paragraphs:
        study_tokens = _significant_tokens(study_para)
        for manuscript_para in manuscript_paragraphs:
            shared = study_tokens & _significant_tokens(manuscript_para)
            if len(shared) >= _MIN_SHARED_CROSS_ROOM and study_para != manuscript_para:
                warnings.append({
                    "label": "warning",
                    "text": "possible contradiction between study canon and manuscript ground",
                    "study_path": "study/canon.md",
                    "manuscript_path": "manuscript/ground.md",
                    "shared_terms": sorted(shared),
                })
    return warnings


def scan_superseded_in_ground(
    conn: sqlite3.Connection,
    root: Path,
) -> list[dict]:
    """Weather law: superseded canon must not remain verbatim in ground files."""
    warnings: list[dict] = []
    rows = conn.execute(
        "SELECT id, body FROM entries WHERE bucket = 'superseded_canon'"
    ).fetchall()
    for room in list_rooms(root):
        if not room.ground or not room.ground_file:
            continue
        rel_path = f"{room.id}/{room.ground_file}"
        file_path = root / rel_path
        if not file_path.exists():
            continue
        file_text = file_path.read_text(encoding="utf-8")
        for row in rows:
            body = str(row["body"]).strip()
            if body and body in file_text:
                warnings.append({
                    "label": "warning",
                    "text": "superseded canon still present in ground file",
                    "path": rel_path,
                    "superseded_entry_id": int(row["id"]),
                })
    return warnings


def scan_contradictions(root: Path, conn: sqlite3.Connection) -> list[dict]:
    """Contradiction gauge — clinical heuristics; reports, never auto-fixes."""
    warnings: list[dict] = []
    study_paragraphs: list[str] = []
    manuscript_paragraphs: list[str] = []

    for room in list_rooms(root):
        if not room.ground or not room.ground_file:
            continue
        rel_path = f"{room.id}/{room.ground_file}"
        paragraphs = _paragraphs(root / rel_path)
        warnings.extend(_paragraph_contradictions(paragraphs, path=rel_path))
        if room.id == "study":
            study_paragraphs = paragraphs
        elif room.id == "manuscript":
            manuscript_paragraphs = paragraphs

    if study_paragraphs and manuscript_paragraphs:
        warnings.extend(_cross_room_contradictions(study_paragraphs, manuscript_paragraphs))

    warnings.extend(scan_superseded_in_ground(conn, root))
    return warnings


def scan_drawer_drift(root: Path, conn: sqlite3.Connection) -> list[dict]:
    """Silent edit detection — latest adoption snapshot vs on-disk file."""
    warnings: list[dict] = []
    for room in list_rooms(root):
        if not room.ground or not room.ground_file:
            continue
        rel_path = f"{room.id}/{room.ground_file}"
        record_id = latest_adoption_for_ground_path(conn, rel_path)
        if record_id is None:
            continue
        warnings.extend(check_drawer(root / rel_path, conn, record_id))
    return warnings


def scan_ground_warnings(root: Path, conn: sqlite3.Connection) -> list[dict]:
    """All ground-room warnings for inhale: drift first, then contradictions."""
    return scan_drawer_drift(root, conn) + scan_contradictions(root, conn)


# Back-compat alias used by early layer 3 tests
scan_ground_drawers = scan_drawer_drift
