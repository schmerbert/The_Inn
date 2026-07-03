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
    shutil.copytree(REPO / "woods", tmp_path / "woods")
    (tmp_path / ".inn").mkdir(exist_ok=True)
    forest.init_db(inn_root := tmp_path)
    return inn_root
