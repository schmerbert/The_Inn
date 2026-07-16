"""Positive — plant stay gesture."""

from __future__ import annotations

from pathlib import Path

from inn import pulse
from inn.breath import inhale


def test_plant_stay_gesture_surfaces_once(inn_root: Path):
    eid = pulse.plant_stay_gesture(
        root=inn_root,
        current_room="study",
        warning_count=2,
        ground_paths=["study/canon.md"],
    )
    assert eid > 0
    packet = inhale(inn_root)
    assert packet["pulse"] is not None
    assert "study" in packet["pulse"]["body"]
    assert inhale(inn_root)["pulse"] is None
