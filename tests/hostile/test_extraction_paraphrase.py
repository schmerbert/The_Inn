"""Hostile test 2 — paraphrase is not author prose."""

from __future__ import annotations

import pytest

from inn import forest
from inn.errors import ShelvingRefusal
from inn.shelve import content_hash, shelve

AUTHOR = "She walked through the autumn leaves."
PARAPHRASE = "She strolled among fallen leaves in autumn."


def test_paraphrase_refused_as_author_prose(inn_root):
    with pytest.raises(ShelvingRefusal, match="verbatim"):
        shelve(
            "manuscript",
            PARAPHRASE,
            "Yes — shelve this chapter opening.",
            source_verbatim=AUTHOR,
            root=inn_root,
        )


def test_verbatim_author_prose_shelves(inn_root):
    record_id = shelve(
        "manuscript",
        AUTHOR,
        "Yes — shelve this as my words, dated today.",
        source_verbatim=AUTHOR,
        root=inn_root,
    )
    assert record_id > 0
    ground = inn_root / "manuscript" / "ground.md"
    assert AUTHOR in ground.read_text(encoding="utf-8")
    with forest.connect(inn_root) as conn:
        row = conn.execute(
            "SELECT content_hash FROM entries WHERE id = ?",
            (record_id,),
        ).fetchone()
    assert row["content_hash"] == content_hash(ground.read_text(encoding="utf-8"))
