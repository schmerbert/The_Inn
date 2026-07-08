"""Layer 4 — inhale remains deterministic for same woods + session state."""

from __future__ import annotations

from inn import forest
from inn.breath import inhale
from inn.session import SessionState, save


def test_inhale_deterministic_for_same_state(inn_root):
    with forest.connect(inn_root) as conn:
        pair_id, _ = forest.insert_pair(
            conn,
            guest_words="Should I lock this chapter order now?",
            innkeeper_words="Not yet; keep it as open pressure.",
        )
        q_id = forest.refuse_ground_invention(
            conn,
            detail="chapter order still unknown",
            pair_root_id=pair_id,
        )
        conn.commit()

    save(
        SessionState(
            current_room="manuscript",
            proximity="chapter-order",
            last_pair_root_id=pair_id,
            seam={"files_in_flight": []},
        ),
        inn_root,
    )

    packet_a = inhale(inn_root)
    packet_b = inhale(inn_root)

    assert packet_a == packet_b
    assert any(row["id"] == q_id for row in packet_a["pressure"])
