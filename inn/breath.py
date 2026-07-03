# breath — inhale/exhale packet assembly (layer 1 stub).
#
# Stores: packet schema only at M0
# Refuses: exhale (not implemented layer 1), automation claims before M1
# Returns: inhale_packet dict
# Test: manual parity ladder BUILD_SPEC § Breath growth

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from inn.errors import BreathRefusal
from inn.paths import repo_root
from inn.rooms import list_rooms, load_room
from inn.session import load as load_session, touch_inhale


def _read_standing_context(root: Path) -> str:
    path = root / "hearth.json"
    if not path.exists():
        return ""
    import json as _json

    data = _json.loads(path.read_text(encoding="utf-8"))
    return str(data.get("standing_context", "") or "")


def _hearth_image_path(root: Path) -> str | None:
    for name in ("hearth.jpg", "hearth.png", "hearth.webp"):
        candidate = root / "assets" / "hearth" / name
        if candidate.exists():
            return str(candidate.relative_to(root)).replace("\\", "/")
    return None


def empty_packet(root: Path | None = None) -> dict[str, Any]:
    """M0 schema — all slots present, unfilled."""
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
            "shelve": "inn.shelve.shelve",
        },
        "hearth_image": _hearth_image_path(root),
    }


def inhale(root: Path | None = None) -> dict[str, Any]:
    """M0 — empty fitted packet; records inhale timestamp."""
    root = root or repo_root()
    touch_inhale(root)
    return empty_packet(root)


def exhale(root: Path | None = None) -> dict[str, Any]:
    raise BreathRefusal("exhale not implemented until layer 5 (M2 manual first)")


def inhale_json(root: Path | None = None) -> str:
    return json.dumps(inhale(root), indent=2)
