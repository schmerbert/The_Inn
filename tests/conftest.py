"""Shared fixtures for hostile tests."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from inn import forest


REPO = Path(__file__).resolve().parent.parent


@pytest.fixture
def inn_root(tmp_path: Path) -> Path:
    for name in ("rooms.yaml", "hearth.json"):
        shutil.copy2(REPO / name, tmp_path / name)
    for room in ("manuscript", "study", "desk", "visitors"):
        shutil.copytree(REPO / room, tmp_path / room)
        # Stay prose is not clinical fixture — wipe ground drawers.
        room_dir = tmp_path / room
        for ground in room_dir.glob("*.md"):
            if ground.name != "room.yaml":
                ground.write_text("", encoding="utf-8")
    woods = tmp_path / "woods"
    woods.mkdir()
    shutil.copy2(REPO / "woods" / "schema.sql", woods / "schema.sql")
    (tmp_path / ".inn").mkdir(exist_ok=True)
    forest.init_db(inn_root := tmp_path)
    return inn_root
