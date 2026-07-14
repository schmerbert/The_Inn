"""Cold wake — python -m inn breathe works without a prior init step."""

from __future__ import annotations

import shutil
from pathlib import Path

from inn import forest


def test_inhale_inits_woods_on_first_wake(tmp_path: Path):
    repo = Path(__file__).resolve().parent.parent.parent
    for name in ("rooms.yaml", "hearth.json"):
        shutil.copy2(repo / name, tmp_path / name)
    for room in ("manuscript", "study", "desk", "visitors"):
        shutil.copytree(repo / room, tmp_path / room)
        for ground in (tmp_path / room).glob("*.md"):
            ground.write_text("", encoding="utf-8")
    woods = tmp_path / "woods"
    woods.mkdir()
    shutil.copy2(repo / "woods" / "schema.sql", woods / "schema.sql")
    (tmp_path / ".inn").mkdir(exist_ok=True)

    from inn.breath import inhale

    packet = inhale(tmp_path)
    assert packet["warnings"] == []
    assert forest.db_path(tmp_path).exists()
