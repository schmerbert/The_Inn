"""Positive — Burial happy path."""

from __future__ import annotations

from pathlib import Path

from inn import forest
from inn.seal import bury


def test_bury_draft_happy(inn_root: Path):
    forest.init_db(inn_root)
    with forest.connect(inn_root) as conn:
        eid = forest.insert(
            conn,
            forest="home",
            bucket="draft",
            signature="model",
            authority="draft",
            body="A draft we will bury.",
            is_pair_root=True,
        )
        conn.commit()

    out = bury(
        eid,
        "Please bury this draft — seal it at my word.",
        root=inn_root,
    )
    assert out["sealing_record_id"] > 0
    assert out["ground_redacted"] is False
