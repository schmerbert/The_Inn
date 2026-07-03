"""Hostile test 1 — praise is not adoption."""

from __future__ import annotations

import pytest

from inn.errors import ShelvingRefusal
from inn.shelve import shelve


def test_praise_alone_refused(inn_root):
    with pytest.raises(ShelvingRefusal, match="enthusiasm is not adoption"):
        shelve(
            "study",
            "She walked through the autumn leaves.",
            "oh, that's lovely",
            root=inn_root,
        )


@pytest.mark.xfail(strict=True, reason="layer 2: happy-path Shelving not implemented")
def test_explicit_adoption_shelves_to_study(inn_root):
    shelve(
        "study",
        "She walked through the autumn leaves.",
        "Yes — shelve this as canon, dated today.",
        source_verbatim="She walked through the autumn leaves.",
        root=inn_root,
    )
