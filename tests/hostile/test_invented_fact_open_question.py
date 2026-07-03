"""Hostile test 3 — invented fact becomes open question, not canon."""

from __future__ import annotations

from inn import forest


def test_invented_fact_lands_in_question_bucket(inn_root):
    with forest.connect(inn_root) as conn:
        pair_id = forest.insert_pair_root(
            conn,
            signature="model",
            body="User: when did the war end?",
        )
        q_id = forest.refuse_ground_invention(
            conn,
            detail="year the war ended — never established",
            pair_root_id=pair_id,
        )
        conn.commit()

        row = conn.execute(
            "SELECT bucket, authority FROM entries WHERE id = ?",
            (q_id,),
        ).fetchone()
        assert row["bucket"] == "question"
        assert row["authority"] != "ground"

        canon = conn.execute(
            "SELECT COUNT(*) AS n FROM entries WHERE bucket = 'adoption_record'"
        ).fetchone()["n"]
        assert canon == 0
