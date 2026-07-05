"""Hostile tests — contradiction gauge on ground rooms."""

from __future__ import annotations

from inn import forest
from inn.breath import inhale
from inn.compare import scan_contradictions
from inn.shelve import shelve


def test_study_paragraphs_that_share_subject_but_differ_warn(inn_root):
    canon = inn_root / "study" / "canon.md"
    canon.parent.mkdir(parents=True, exist_ok=True)
    canon.write_text(
        "The treaty was signed in spring.\n\nThe treaty was signed in autumn.",
        encoding="utf-8",
    )

    with forest.connect(inn_root) as conn:
        warnings = scan_contradictions(inn_root, conn)

    assert any("possible contradiction between ground paragraphs" in w["text"] for w in warnings)


def test_study_and_manuscript_cross_room_contradiction_warns(inn_root):
    (inn_root / "study").mkdir(parents=True, exist_ok=True)
    (inn_root / "manuscript").mkdir(parents=True, exist_ok=True)
    (inn_root / "study" / "canon.md").write_text(
        "Kaelen died at the siege camp before winter.",
        encoding="utf-8",
    )
    (inn_root / "manuscript" / "ground.md").write_text(
        "Kaelen walked to the siege camp at dawn.",
        encoding="utf-8",
    )

    with forest.connect(inn_root) as conn:
        warnings = scan_contradictions(inn_root, conn)

    assert any(
        "study canon and manuscript ground" in w["text"] for w in warnings
    )


def test_inhale_includes_contradiction_warnings(inn_root):
    (inn_root / "study").mkdir(parents=True, exist_ok=True)
    (inn_root / "study" / "canon.md").write_text(
        "The treaty was signed in spring.\n\nThe treaty was signed in autumn.",
        encoding="utf-8",
    )

    packet = inhale(inn_root)
    assert any(
        "possible contradiction" in w.get("text", "") for w in packet["warnings"]
    )


def test_reshelve_same_drawer_builds_adoption_chain(inn_root):
    first = shelve(
        "study",
        "The treaty was signed in spring.",
        "Yes — shelve the spring fact.",
        root=inn_root,
    )
    second = shelve(
        "study",
        "The alliance held through winter.",
        "Yes — shelve the winter fact too.",
        root=inn_root,
    )

    with forest.connect(inn_root) as conn:
        rows = conn.execute(
            """
            SELECT id FROM entries
            WHERE bucket = 'adoption_record'
              AND json_extract(meta_json, '$.ground_path') = 'study/canon.md'
            ORDER BY id ASC
            """
        ).fetchall()
        edge = conn.execute(
            "SELECT kind FROM edges WHERE from_id = ? AND to_id = ?",
            (second, first),
        ).fetchone()

    assert [int(r["id"]) for r in rows] == [first, second]
    assert edge is not None
    assert edge["kind"] == "cites"

    packet = inhale(inn_root)
    study_ground = next(g for g in packet["ground"] if g["room_id"] == "study")
    assert study_ground["adoption_record_ids"] == [first, second]
    assert study_ground["adoption_record_id"] == second
