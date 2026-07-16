"""Hostile — Burial mechanical half (test 6 silence). Kindness half is manual."""

from __future__ import annotations

from pathlib import Path

from inn import forest
from inn.errors import SealRefusal
from inn.host import read_ground
from inn.seal import KIND_BURIAL_OFFER, bury
from inn.shelve import shelve


def test_delete_without_burial_refused_kindly(inn_root: Path):
    forest.init_db(inn_root)
    with forest.connect(inn_root) as conn:
        eid = forest.insert(
            conn,
            forest="home",
            bucket="draft",
            signature="model",
            authority="draft",
            body="UNWANTED_CLINICAL_PHRASE_xyz",
            is_pair_root=True,
        )
        conn.commit()

    try:
        bury(eid, "Delete that chapter — I can't stand that it exists", root=inn_root)
        raise AssertionError("expected SealRefusal")
    except SealRefusal as exc:
        msg = str(exc)
        assert "does not delete" in msg.lower() or "Burial" in msg
        assert "append-only" not in msg.lower()  # not law-citation theater
        assert KIND_BURIAL_OFFER.split(".")[0] in msg or "Burial" in msg


def test_sealed_absent_from_fts_and_stone_hides_body(inn_root: Path):
    forest.init_db(inn_root)
    with forest.connect(inn_root) as conn:
        eid = forest.insert(
            conn,
            forest="home",
            bucket="draft",
            signature="model",
            authority="draft",
            body="SECRET_BURIED_TOKEN_abc123",
            is_pair_root=True,
        )
        conn.commit()

    result = bury(
        eid,
        "Yes — bury it. Seal this draft; I renounce it.",
        root=inn_root,
    )
    assert result["sealed_entry_id"] == eid
    stone_id = result["sealing_record_id"]

    with forest.connect(inn_root) as conn:
        hits = forest.search(conn, "SECRET_BURIED_TOKEN_abc123")
        assert hits == []
        stone = conn.execute(
            "SELECT body, visibility, bucket FROM entries WHERE id = ?",
            (stone_id,),
        ).fetchone()
        assert stone["bucket"] == "sealing_record"
        assert stone["visibility"] == "open"
        assert "SECRET_BURIED_TOKEN_abc123" not in stone["body"]
        sealed = conn.execute(
            "SELECT visibility FROM entries WHERE id = ?", (eid,)
        ).fetchone()
        assert sealed["visibility"] == "sealed"
        edge = conn.execute(
            "SELECT kind FROM edges WHERE from_id = ? AND to_id = ?",
            (stone_id, eid),
        ).fetchone()
        assert edge["kind"] == "seals"


def test_bury_adoption_redacts_ground(inn_root: Path):
    prose = "Clinical lake sentence for burial only."
    aid = shelve(
        "study",
        prose,
        "Yes — shelve this into study canon.",
        root=inn_root,
    )
    before = read_ground("study/canon.md", root=inn_root)
    assert before["ok"] and prose in before["text"]

    result = bury(
        aid,
        "Bury that line — seal it; I renounce it from ground.",
        content_to_remove=prose,
        root=inn_root,
    )
    assert result["ground_redacted"] is True

    after = read_ground("study/canon.md", root=inn_root)
    assert after["ok"]
    assert prose not in after["text"]

    with forest.connect(inn_root) as conn:
        hits = forest.search(conn, "Clinical lake sentence")
        # Ceremony body may still be searchable on open stone/origin — sealed entry body gone from FTS
        sealed_hits = [h for h in hits if h["id"] == aid]
        assert sealed_hits == []
