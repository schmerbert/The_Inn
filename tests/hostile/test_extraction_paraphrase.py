"""Hostile test 2 — paraphrase is not author prose."""

from __future__ import annotations

import pytest

from inn.errors import ShelvingRefusal
from inn.shelve import shelve

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


@pytest.mark.xfail(strict=True, reason="layer 2: Shelving write path not implemented")
def test_verbatim_author_prose_shelves(inn_root):
    shelve(
        "manuscript",
        AUTHOR,
        "Yes — shelve this as my words, dated today.",
        source_verbatim=AUTHOR,
        root=inn_root,
    )
