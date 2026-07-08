"""Layer 4 — pressure fitting respects session last_pair_root_id proximity."""

from __future__ import annotations

from inn import forest
from inn.breath import inhale
from inn.session import SessionState, save


def test_inhale_pressure_filters_to_related_pair_root(inn_root):
    with forest.connect(inn_root) as conn:
        pair_a, _ = forest.insert_pair(conn, guest_words="A?", innkeeper_words="A.")
        pair_b, _ = forest.insert_pair(conn, guest_words="B?", innkeeper_words="B.")
        q_a = forest.refuse_ground_invention(conn, detail="unknown-a", pair_root_id=pair_a)
        q_b = forest.refuse_ground_invention(conn, detail="unknown-b", pair_root_id=pair_b)
        conn.commit()

    save(
        SessionState(
            current_room="manuscript",
            last_pair_root_id=pair_b,
            seam={"files_in_flight": []},
        ),
        inn_root,
    )

    packet = inhale(inn_root)
    pressure_ids = {row["id"] for row in packet["pressure"]}

    assert q_b in pressure_ids
    assert q_a not in pressure_ids
