"""Positive — rebind_ground clears drawer drift without appending."""

from __future__ import annotations

from pathlib import Path

from inn.compare import file_hash, latest_adoption_for_ground_path, scan_drawer_drift
from inn import forest
from inn.shelve import rebind_ground, shelve


def test_rebind_clears_drift(inn_root: Path):
    shelve(
        "study",
        "Original shelved line.",
        "Yes — shelve this into study canon.",
        root=inn_root,
    )
    path = inn_root / "study" / "canon.md"
    # Silent edit — classic drift.
    path.write_text("Original shelved line.\n\nSilent append.\n", encoding="utf-8")

    with forest.connect(inn_root) as conn:
        before = scan_drawer_drift(inn_root, conn)
    assert any("does not match" in w.get("text", "") for w in before)

    rid = rebind_ground(
        "study",
        "Yes — rebind study trailhead after silent edit.",
        root=inn_root,
    )
    assert rid > 0
    # File text unchanged (no append of adopting words).
    assert "rebind study trailhead" not in path.read_text(encoding="utf-8")

    with forest.connect(inn_root) as conn:
        latest = latest_adoption_for_ground_path(conn, "study/canon.md")
        row = conn.execute(
            "SELECT content_hash FROM entries WHERE id = ?", (latest,)
        ).fetchone()
        assert row["content_hash"] == file_hash(path)
        after = scan_drawer_drift(inn_root, conn)
    assert after == []
