"""Layer 4 — inhale writes append-only breath receipt."""

from __future__ import annotations

import json

from inn.breath import inhale


def test_inhale_writes_breath_receipt_with_timings(inn_root):
    packet = inhale(inn_root)
    assert packet["posture"] == "guest"

    files = sorted((inn_root / "logs" / "breath").glob("*-inhale.json"))
    assert len(files) == 1

    receipt = json.loads(files[0].read_text(encoding="utf-8"))
    assert receipt["kind"] == "inhale_receipt"
    assert set(receipt["timings_ms"]).issuperset({"warnings", "ground", "pressure", "total"})
    assert receipt["slot_counts"]["warnings"] == len(packet["warnings"])
    assert receipt["slot_counts"]["ground"] == len(packet["ground"])
    assert receipt["slot_counts"]["pressure"] == len(packet["pressure"])
