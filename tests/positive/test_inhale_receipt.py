"""Layer 4.5 — inhale receipt lists every non-empty slot by id/path."""

from __future__ import annotations

import json

from inn import forest
from inn.breath import inhale
from inn.shelve import shelve


def test_inhale_receipt_lists_nonempty_slots_by_id(inn_root):
    shelve(
        "study",
        "The treaty was signed in spring.",
        "Yes — shelve that as canon.",
        root=inn_root,
    )
    with forest.connect(inn_root) as conn:
        pair_id = forest.insert_pair_root(conn, signature="model", body="session")
        q_id = forest.refuse_ground_invention(
            conn,
            detail="unknown siege date",
            pair_root_id=pair_id,
        )
        conn.commit()

    packet = inhale(inn_root)
    files = sorted((inn_root / "logs" / "breath").glob("*-inhale.json"))
    assert len(files) == 1
    receipt = json.loads(files[0].read_text(encoding="utf-8"))

    assert receipt["kind"] == "inhale_receipt"
    assert q_id in receipt["slot_ids"]["pressure"]
    assert receipt["slot_ids"]["ground_adoption_records"]
    assert receipt["slot_counts"]["ground"] == len(packet["ground"])
    assert receipt["slot_counts"]["pressure"] == len(packet["pressure"])
    assert receipt["slot_counts"]["warnings"] == len(packet["warnings"])
    assert set(receipt["timings_ms"]) >= {"warnings", "ground", "pressure", "total"}
