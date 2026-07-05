"""Positive path — author adopts words; full trail lands."""

from __future__ import annotations

import json

from inn import forest
from inn.shelve import content_hash, shelve

AUTHOR = "The treaty was signed in spring."
ADOPTING = 'Yes — "The treaty was signed in spring" is canon now, dated today.'


def test_shelve_study_canon_with_adoption_record(inn_root):
    record_id = shelve(
        "study",
        AUTHOR,
        ADOPTING,
        root=inn_root,
    )

    ground = inn_root / "study" / "canon.md"
    file_text = ground.read_text(encoding="utf-8")
    assert AUTHOR in file_text

    with forest.connect(inn_root) as conn:
        record = conn.execute(
            "SELECT bucket, body, body_hash, content_hash, signature, meta_json FROM entries WHERE id = ?",
            (record_id,),
        ).fetchone()
        edge = conn.execute(
            "SELECT kind FROM edges WHERE from_id = ?",
            (record_id,),
        ).fetchone()

    assert record["bucket"] == "adoption_record"
    assert record["signature"] == "author"
    assert record["body"] == ADOPTING
    assert record["body_hash"] == content_hash(ADOPTING)
    assert record["content_hash"] == content_hash(file_text)
    meta = json.loads(record["meta_json"])
    assert meta["ground_path"] == "study/canon.md"
    assert edge["kind"] == "adopts"
