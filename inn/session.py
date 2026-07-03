# session — .inn/session.yaml load/save.
#
# Stores: current_room, proximity, seam, last_pair_root_id
# Refuses: invalid room ids on save
# Returns: SessionState dict
# Test: tests/hostile/ (indirect via breath)

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from inn.errors import RoomRefusal
from inn.paths import repo_root
from inn.rooms import default_room_id, load_room


@dataclass
class SessionState:
    current_room: str
    proximity: str | None = None
    last_inhale_at: str | None = None
    last_pair_root_id: int | None = None
    seam: dict[str, Any] = field(default_factory=lambda: {"files_in_flight": []})

    def to_dict(self) -> dict[str, Any]:
        out: dict[str, Any] = {
            "current_room": self.current_room,
            "seam": self.seam,
        }
        if self.proximity is not None:
            out["proximity"] = self.proximity
        if self.last_inhale_at is not None:
            out["last_inhale_at"] = self.last_inhale_at
        if self.last_pair_root_id is not None:
            out["last_pair_root_id"] = self.last_pair_root_id
        return out

    @classmethod
    def from_dict(cls, data: dict[str, Any], root: Path | None = None) -> SessionState:
        root = root or repo_root()
        room = data.get("current_room") or default_room_id(root)
        load_room(room, root)
        seam = data.get("seam") or {"files_in_flight": []}
        return cls(
            current_room=room,
            proximity=data.get("proximity"),
            last_inhale_at=data.get("last_inhale_at"),
            last_pair_root_id=data.get("last_pair_root_id"),
            seam=seam,
        )


def session_path(root: Path | None = None) -> Path:
    root = root or repo_root()
    return root / ".inn" / "session.yaml"


def load(root: Path | None = None) -> SessionState:
    root = root or repo_root()
    path = session_path(root)
    if not path.exists():
        return SessionState(current_room=default_room_id(root))
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return SessionState.from_dict(data, root)


def save(state: SessionState, root: Path | None = None) -> None:
    root = root or repo_root()
    load_room(state.current_room, root)
    path = session_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(state.to_dict(), sort_keys=False), encoding="utf-8")


def set_room(room_id: str, root: Path | None = None) -> SessionState:
    root = root or repo_root()
    load_room(room_id, root)
    state = load(root)
    state.current_room = room_id
    save(state, root)
    return state


def touch_inhale(root: Path | None = None) -> SessionState:
    state = load(root)
    state.last_inhale_at = datetime.now(timezone.utc).isoformat()
    save(state, root)
    return state
