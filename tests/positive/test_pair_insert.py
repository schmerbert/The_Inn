"""Layer 4 — pair insert trailhead for message ingest."""

from __future__ import annotations

from inn import forest


def test_insert_pair_records_guest_and_response_with_edge(inn_root):
    with forest.connect(inn_root) as conn:
        pair_root_id, response_id = forest.insert_pair(
            conn,
            guest_words="Could the treaty be broken by winter?",
            innkeeper_words="Unknown on current canon; should be recorded as question.",
        )
        conn.commit()

        assert pair_root_id > 0
        assert response_id is not None

        guest = conn.execute(
            "SELECT bucket, authority FROM entries WHERE id = ?",
            (pair_root_id,),
        ).fetchone()
        assert guest["bucket"] == "session_pair"
        assert guest["authority"] == "stranger"

        reply = conn.execute(
            "SELECT bucket, authority FROM entries WHERE id = ?",
            (response_id,),
        ).fetchone()
        assert reply["bucket"] == "session_pair"
        assert reply["authority"] == "model"

        edge = conn.execute(
            "SELECT kind FROM edges WHERE from_id = ? AND to_id = ?",
            (response_id, pair_root_id),
        ).fetchone()
        assert edge["kind"] == "responds_to"
