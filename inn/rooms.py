# rooms — load room registry and per-room policy manifests.
#
# Stores: rooms.yaml, */room.yaml
# Refuses: unknown room ids, malformed manifests
# Returns: RoomPolicy dataclass, registry list
# Test: tests/hostile/test_shelve_praise_not_adoption.py (via shelve)

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from inn.errors import RoomRefusal
from inn.paths import repo_root


@dataclass
class RoomPolicy:
    id: str
    label: str
    posture: str
    write: list[str]
    ground: bool
    crossings: list[str]
    refuses: list[str]
    path: Path

    def allows_crossing(self, crossing: str) -> bool:
        return crossing in self.crossings

    def allows_write(self, mode: str) -> bool:
        if "deny" in self.write or "all_writes" in self.refuses:
            return False
        return mode in self.write


def _normalize_write(raw: Any) -> list[str]:
    if raw is None:
        return []
    if isinstance(raw, str):
        return [raw]
    return list(raw)


def load_registry(root: Path | None = None) -> dict[str, Any]:
    root = root or repo_root()
    path = root / "rooms.yaml"
    if not path.exists():
        raise RoomRefusal(f"rooms.yaml missing at {path}")
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if "rooms" not in data:
        raise RoomRefusal("rooms.yaml must define 'rooms'")
    return data


def load_room(room_id: str, root: Path | None = None) -> RoomPolicy:
    root = root or repo_root()
    registry = load_registry(root)
    if room_id not in registry["rooms"]:
        raise RoomRefusal(f"unknown room id: {room_id}")

    room_dir = root / room_id
    manifest = room_dir / "room.yaml"
    if not manifest.exists():
        raise RoomRefusal(f"room manifest missing: {manifest}")

    data = yaml.safe_load(manifest.read_text(encoding="utf-8")) or {}
    if data.get("id") != room_id:
        raise RoomRefusal(f"room.yaml id mismatch: {data.get('id')} != {room_id}")

    perms = data.get("permissions") or {}
    return RoomPolicy(
        id=room_id,
        label=str(data.get("label", room_id)),
        posture=str(data.get("posture", "")).strip(),
        write=_normalize_write(perms.get("write")),
        ground=bool(perms.get("ground", False)),
        crossings=list(data.get("crossings") or []),
        refuses=list(data.get("refuses") or []),
        path=room_dir,
    )


def list_rooms(root: Path | None = None) -> list[RoomPolicy]:
    registry = load_registry(root)
    return [load_room(rid, root) for rid in registry["rooms"]]


def default_room_id(root: Path | None = None) -> str:
    registry = load_registry(root)
    return str(registry.get("default", registry["rooms"][0]))
