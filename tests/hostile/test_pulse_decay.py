"""Hostile — faun pulse must die after one arrival; unsigned refused."""

from __future__ import annotations

from pathlib import Path

from inn import forest, pulse
from inn.breath import inhale
from inn.errors import ForestRefusal


def test_unsigned_pulse_refused(inn_root: Path):
    try:
        pulse.plant("hello", signature="", root=inn_root)
        raise AssertionError("expected ForestRefusal")
    except ForestRefusal as exc:
        assert "unsigned" in str(exc).lower()


def test_pulse_dies_after_one_inhale(inn_root: Path):
    pulse.plant(
        "FAUN_PULSE:\n—f clinical gesture only",
        root=inn_root,
    )
    first = inhale(inn_root)
    assert first.get("pulse") is not None
    assert first["pulse"]["signature"] == "faun"
    assert first["pulse"]["voice"] == "faun"
    assert "FAUN_PULSE" in first["pulse"]["body"]

    second = inhale(inn_root)
    assert second.get("pulse") is None


def test_pulse_not_in_ground_slot(inn_root: Path):
    pulse.plant("FAUN_PULSE:\n—f pointer", root=inn_root)
    packet = inhale(inn_root)
    assert packet["pulse"] is not None
    # Ground slot is adoption/file index only — pulse body must not appear there.
    blob = str(packet.get("ground"))
    assert "FAUN_PULSE" not in blob
    assert "—f pointer" not in blob
