"""Positive — exhale seat check (layer 5)."""

from __future__ import annotations

import time
from pathlib import Path

import pytest

from inn import breath, forest
from inn.errors import BreathRefusal
from inn.host import ingest_turn, wake


def test_exhale_clear_when_handoff_fresh(inn_root: Path):
    (inn_root / "HANDOFF.md").write_text("# handoff\nok\n", encoding="utf-8")
    wake(inn_root)
    # HANDOFF after woods activity
    time.sleep(0.05)
    (inn_root / "HANDOFF.md").write_text("# handoff\nupdated\n", encoding="utf-8")
    result = breath.exhale(inn_root)
    assert result["clear"] is True
    assert result["held"] == []


def test_exhale_refuses_stale_handoff(inn_root: Path):
    handoff = inn_root / "HANDOFF.md"
    handoff.write_text("# old\n", encoding="utf-8")
    # Force handoff clearly older than subsequent woods inserts (Windows mtime granularity).
    past = time.time() - 120
    import os

    os.utime(handoff, (past, past))
    wake(inn_root)
    ingest_turn("hello?", "hi from guest", root=inn_root)
    with pytest.raises(BreathRefusal, match="HANDOFF older"):
        breath.exhale(inn_root)


def test_exhale_refuses_without_inhale(inn_root: Path):
    (inn_root / "HANDOFF.md").write_text("# handoff\n", encoding="utf-8")
    forest.init_db(inn_root)
    with pytest.raises(BreathRefusal, match="no inhale"):
        breath.exhale(inn_root)
