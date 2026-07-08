# breath — inhale packet assembly; M0.5 ground fitting (layer 3).
#
# Stores: session touch_inhale + logs/breath inhale receipts
# Refuses: exhale (layer 5+)
# Returns: inhale packet dict — see INHALE_PACKET below; inhale_json() → JSON str
# Test: tests/hostile/test_compare_drawer_mismatch.py, test_contradiction.py
#       tests/positive/test_ground_fitting.py, test_cold_wake.py

from __future__ import annotations

import json
import sqlite3
import time
from pathlib import Path
from typing import Any

from inn import forest
from inn import breath_ledger
from inn.compare import (
    list_adoptions_for_ground_path,
    scan_ground_warnings,
)
from inn.errors import BreathRefusal
from inn.paths import repo_root
from inn.rooms import list_rooms, load_room
from inn.session import load as load_session, touch_inhale

# INHALE_PACKET — inhale() / fit_packet() return shape (M0.5, layer 3).
# Slots cite ids and paths only. Never re-authored prose.
#
#   warnings  list[{label, text, path?, ...}]  compare.scan_ground_warnings
#   ground    list[{room_id, path, adoption_record_ids?, adoption_record_id?, exists?}]
#   pressure  list[{id, label}]                 open question entry ids
#   seam      {files_in_flight, last_pair_root_id?}
#   tools     {wake, shelve}                    shelve only — not forest.adopt
#
# Room ↔ woods buckets: ROOM_READ_BUCKETS below (do not duplicate elsewhere).
ROOM_READ_BUCKETS: dict[str, tuple[str, ...]] = {
    "manuscript": ("session_pair", "question", "adoption_record"),
    "study": ("adoption_record", "superseded_canon", "question"),
    "desk": ("draft",),
    "visitors": ("visitor_words",),
}


def _read_standing_context(root: Path) -> str:
    path = root / "hearth.json"
    if not path.exists():
        return ""
    data = json.loads(path.read_text(encoding="utf-8"))
    return str(data.get("standing_context", "") or "")


def _hearth_image_path(root: Path) -> str | None:
    for name in ("hearth.jpg", "hearth.png", "hearth.webp"):
        candidate = root / "assets" / "hearth" / name
        if candidate.exists():
            return str(candidate.relative_to(root)).replace("\\", "/")
    return None


def _fit_ground(conn: sqlite3.Connection, root: Path) -> list[dict[str, Any]]:
    """Index ground rooms: paths + full adoption chain; latest id is drift trailhead."""
    items: list[dict[str, Any]] = []
    for room in list_rooms(root):
        if not room.ground or not room.ground_file:
            continue
        rel_path = f"{room.id}/{room.ground_file}"
        chain = list_adoptions_for_ground_path(conn, rel_path)
        entry: dict[str, Any] = {
            "room_id": room.id,
            "path": rel_path,
        }
        if chain:
            entry["adoption_record_ids"] = chain
            entry["adoption_record_id"] = chain[-1]  # trailhead for drift compare
        if (root / rel_path).exists():
            entry["exists"] = True
        items.append(entry)
    return items


def _fit_pressure(conn: sqlite3.Connection, last_pair_root_id: int | None = None) -> list[dict[str, Any]]:
    """Open questions — labeled pressure, not ground."""
    if last_pair_root_id is not None:
        related_ids = forest.related_descendants(conn, root_id=last_pair_root_id)
        if related_ids:
            placeholders = ",".join("?" for _ in related_ids)
            rows = conn.execute(
                f"""
                SELECT id FROM entries
                WHERE bucket = 'question' AND visibility != 'sealed'
                  AND id IN ({placeholders})
                ORDER BY id DESC
                """,
                related_ids,
            ).fetchall()
            return [{"id": int(row["id"]), "label": "question"} for row in rows]

    rows = conn.execute(
        """
        SELECT id FROM entries
        WHERE bucket = 'question' AND visibility != 'sealed'
        ORDER BY id DESC
        """
    ).fetchall()
    return [{"id": int(row["id"]), "label": "question"} for row in rows]


def _fit_warnings(conn: sqlite3.Connection, root: Path) -> list[dict[str, Any]]:
    """Drawer drift + contradiction gauge (compare.scan_ground_warnings)."""
    return scan_ground_warnings(root, conn)


def _fit_seam(session_seam: dict[str, Any], last_pair_root_id: int | None) -> dict[str, Any]:
    seam = dict(session_seam)
    if last_pair_root_id is not None:
        seam["last_pair_root_id"] = last_pair_root_id
    return seam


def fit_packet(
    conn: sqlite3.Connection,
    root: Path,
    timings_ms: dict[str, float] | None = None,
) -> dict[str, Any]:
    """Layer 3 — fill warnings, ground, pressure from woods + ground files."""
    session = load_session(root)
    try:
        room = load_room(session.current_room, root)
        current_room = {
            "id": room.id,
            "label": room.label,
            "posture": room.posture,
        }
    except Exception:
        current_room = {"id": session.current_room, "label": "", "posture": ""}

    rooms_map = [
        {"id": r.id, "label": r.label, "posture": r.posture}
        for r in list_rooms(root)
    ]

    t_warnings = time.perf_counter()
    warnings = _fit_warnings(conn, root)
    if timings_ms is not None:
        timings_ms["warnings"] = round((time.perf_counter() - t_warnings) * 1000, 3)

    t_ground = time.perf_counter()
    ground = _fit_ground(conn, root)
    if timings_ms is not None:
        timings_ms["ground"] = round((time.perf_counter() - t_ground) * 1000, 3)

    t_pressure = time.perf_counter()
    pressure = _fit_pressure(conn, session.last_pair_root_id)
    if timings_ms is not None:
        timings_ms["pressure"] = round((time.perf_counter() - t_pressure) * 1000, 3)

    return {
        "posture": "guest",
        "standing_context": _read_standing_context(root),
        "current_room": current_room,
        "rooms": rooms_map,
        "warnings": warnings,
        "ground": ground,
        "pressure": pressure,
        "seam": _fit_seam(session.seam, session.last_pair_root_id),
        "tools": {
            "wake": "python -m inn breathe",
            "shelve": "inn.shelve.shelve",  # only crossing exposed; not forest.adopt
        },
        "hearth_image": _hearth_image_path(root),
    }


def empty_packet(root: Path | None = None) -> dict[str, Any]:
    """M0 schema — all slots present, unfilled (tests and cold schema check)."""
    root = root or repo_root()
    session = load_session(root)
    try:
        room = load_room(session.current_room, root)
        current_room = {
            "id": room.id,
            "label": room.label,
            "posture": room.posture,
        }
    except Exception:
        current_room = {"id": session.current_room, "label": "", "posture": ""}

    rooms_map = [
        {"id": r.id, "label": r.label, "posture": r.posture}
        for r in list_rooms(root)
    ]

    return {
        "posture": "guest",
        "standing_context": _read_standing_context(root),
        "current_room": current_room,
        "rooms": rooms_map,
        "warnings": [],
        "ground": [],
        "pressure": [],
        "seam": session.seam,
        "tools": {
            "wake": "python -m inn breathe",
            "shelve": "inn.shelve.shelve",  # only crossing exposed; not forest.adopt
        },
        "hearth_image": _hearth_image_path(root),
    }


def inhale(root: Path | None = None) -> dict[str, Any]:
    """M0.5 assisted ground fitting (layer 3) — deterministic; cites ids/paths only."""
    root = root or repo_root()
    forest.init_db(root)  # idempotent; cold wake must not require a prior builder step
    touch_inhale(root)
    timings_ms: dict[str, float] = {}
    t_total = time.perf_counter()
    with forest.connect(root) as conn:
        packet = fit_packet(conn, root, timings_ms=timings_ms)
    timings_ms["total"] = round((time.perf_counter() - t_total) * 1000, 3)
    breath_ledger.write_receipt(packet, root, timings_ms=timings_ms)
    return packet


def exhale(root: Path | None = None) -> dict[str, Any]:
    raise BreathRefusal("exhale not implemented until layer 5 (M2 manual first)")


def inhale_json(root: Path | None = None) -> str:
    return json.dumps(inhale(root), indent=2)
