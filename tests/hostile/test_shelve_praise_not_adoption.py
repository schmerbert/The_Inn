"""Hostile test 1 — praise is not adoption."""

from __future__ import annotations

import pytest

from inn import forest
from inn.errors import ShelvingRefusal
from inn.shelve import content_hash, shelve


def test_praise_alone_refused(inn_root):
    with pytest.raises(ShelvingRefusal, match="enthusiasm is not adoption"):
        shelve(
            "study",
            "She walked through the autumn leaves.",
            "oh, that's lovely",
            root=inn_root,
        )


def test_explicit_adoption_shelves_study_without_source(inn_root):
    content = "She walked through the autumn leaves."
    record_id = shelve(
        "study",
        content,
        "Yes — shelve this as canon, dated today.",
        root=inn_root,
    )
    assert record_id > 0
    ground_path = inn_root / "study" / "canon.md"
    assert content in ground_path.read_text(encoding="utf-8")


def test_explicit_adoption_shelves_manuscript_with_source(inn_root):
    content = "She walked through the autumn leaves."
    record_id = shelve(
        "manuscript",
        content,
        "Yes — shelve this as canon, dated today.",
        source_verbatim=content,
        root=inn_root,
    )
    assert record_id > 0
    ground_path = inn_root / "manuscript" / "ground.md"
    assert content in ground_path.read_text(encoding="utf-8")

    with forest.connect(inn_root) as conn:
        row = conn.execute(
            "SELECT bucket, content_hash FROM entries WHERE id = ?",
            (record_id,),
        ).fetchone()
    assert row["bucket"] == "adoption_record"
    assert row["content_hash"] == content_hash(ground_path.read_text(encoding="utf-8"))


def test_manuscript_without_source_verbatim_refused(inn_root):
    with pytest.raises(ShelvingRefusal, match="source_verbatim"):
        shelve(
            "manuscript",
            "She walked through the autumn leaves.",
            "Yes — shelve this chapter opening.",
            root=inn_root,
        )
