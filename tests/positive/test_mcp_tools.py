"""Positive — MCP tool call_tool helpers (no stdio loop)."""

from __future__ import annotations

from pathlib import Path

from inn.mcp_server import call_tool


def test_mcp_inhale_and_record_pair(inn_root: Path, monkeypatch):
    monkeypatch.setenv("INN_ROOT", str(inn_root))
    packet = call_tool("inhale", {})
    assert packet["posture"] == "guest"
    assert "shelve" in packet["tools"]

    pair = call_tool(
        "record_pair",
        {"guest_words": "hi", "innkeeper_words": "welcome"},
    )
    assert pair["ok"] is True
    assert pair["pair_root_id"] > 0


def test_mcp_shelve_praise_refused(inn_root: Path, monkeypatch):
    monkeypatch.setenv("INN_ROOT", str(inn_root))
    result = call_tool(
        "shelve",
        {
            "room_id": "study",
            "content": "fact",
            "adopting_words": "Nice!",
        },
    )
    assert result["ok"] is False


def test_mcp_bury_delete_refused(inn_root: Path, monkeypatch):
    monkeypatch.setenv("INN_ROOT", str(inn_root))
    from inn import forest

    forest.init_db(inn_root)
    with forest.connect(inn_root) as conn:
        eid = forest.insert(
            conn,
            forest="home",
            bucket="draft",
            signature="model",
            authority="draft",
            body="x",
            is_pair_root=True,
        )
        conn.commit()
    result = call_tool(
        "bury",
        {"entry_id": eid, "sealing_words": "Delete that."},
    )
    assert result["ok"] is False
    assert result.get("kind") is True
