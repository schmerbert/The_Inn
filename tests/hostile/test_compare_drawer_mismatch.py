"""Hostile test 5 — silent drawer edit after adoption is detectable."""

from __future__ import annotations

import pytest

from inn import forest
from inn.compare import check_drawer
from inn.shelve import content_hash


def test_compare_detects_drawer_mismatch(inn_root):
    drawer = inn_root / "study" / "canon.md"
    drawer.parent.mkdir(parents=True, exist_ok=True)
    original = "The treaty was signed in spring."
    drawer.write_text(original, encoding="utf-8")

    with forest.connect(inn_root) as conn:
        pair_id = forest.insert_pair_root(conn, signature="author", body="adoption ceremony")
        record_id = forest.insert(
            conn,
            forest="home",
            bucket="adoption_record",
            signature="author",
            authority="ground",
            body=original,
            content_hash=content_hash(original),
            origin_to_id=pair_id,
            origin_kind="adopts",
        )
        conn.commit()

        drawer.write_text(original + "\nSomeone edited this silently.", encoding="utf-8")

        with forest.connect(inn_root) as conn2:
            warnings = check_drawer(drawer, conn2, record_id)

    assert len(warnings) == 1
    assert "does not match adoption trail" in warnings[0]["text"]


@pytest.mark.xfail(strict=True, reason="layer 3: inhale warnings slot not wired to compare")
def test_inhale_surfaces_drawer_mismatch_in_warnings(inn_root):
    from inn.breath import inhale

    packet = inhale(inn_root)
    assert any("does not match" in w.get("text", "") for w in packet["warnings"])
