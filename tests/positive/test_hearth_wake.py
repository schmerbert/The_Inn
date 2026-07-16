"""Positive — hearthstone path on inhale / guest posture."""

from __future__ import annotations

import shutil
from pathlib import Path

from inn.host import guest_system_prompt, wake

REPO = Path(__file__).resolve().parent.parent.parent


def test_inhale_hearth_image_when_present(inn_root: Path):
    src = REPO / "assets" / "hearth" / "hearth.jpg"
    assert src.is_file(), "repo hearthstone missing — layer 6 asset"
    dest_dir = inn_root / "assets" / "hearth"
    dest_dir.mkdir(parents=True)
    shutil.copy2(src, dest_dir / "hearth.jpg")

    packet = wake(inn_root)
    assert packet["hearth_image"] == "assets/hearth/hearth.jpg"
    prompt = guest_system_prompt(packet)
    assert "Hearthstone" in prompt or "hearthstone" in prompt.lower()
    assert "bury" in packet["tools"]


def test_inhale_hearth_image_null_when_absent(inn_root: Path):
    packet = wake(inn_root)
    assert packet.get("hearth_image") is None
