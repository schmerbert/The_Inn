"""Layer 3 — breath ground fitting."""

from __future__ import annotations

from inn import forest
from inn.breath import inhale
from inn.shelve import shelve


def test_inhale_lists_ground_after_shelve(inn_root):
    shelve(
        "study",
        "The treaty was signed in spring.",
        "Yes — shelve that as canon.",
        root=inn_root,
    )

    packet = inhale(inn_root)
    ground = packet["ground"]
    assert any(
        g.get("room_id") == "study"
        and g.get("path") == "study/canon.md"
        and len(g.get("adoption_record_ids", [])) == 1
        and g.get("adoption_record_id") == g["adoption_record_ids"][-1]
        for g in ground
    )


def test_inhale_lists_open_questions_in_pressure(inn_root):
    with forest.connect(inn_root) as conn:
        pair_id = forest.insert_pair_root(conn, signature="model", body="session")
        q_id = forest.refuse_ground_invention(
            conn,
            detail="unknown fact",
            pair_root_id=pair_id,
        )
        conn.commit()

    packet = inhale(inn_root)
    assert any(p.get("id") == q_id and p.get("label") == "question" for p in packet["pressure"])
