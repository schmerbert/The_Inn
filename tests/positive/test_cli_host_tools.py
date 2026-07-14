"""Positive — CLI tool dispatch + mocked chat (no live API)."""

from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import patch

from inn.cli_host import run_guest_turn, run_tool


def test_load_dotenv_does_not_override(inn_root: Path, monkeypatch):
    from inn.cli_host import load_dotenv

    (inn_root / ".env").write_text("INN_API_MODEL=from-file\n", encoding="utf-8")
    monkeypatch.setenv("INN_API_MODEL", "already-set")
    load_dotenv(inn_root)
    assert os.environ["INN_API_MODEL"] == "already-set"

    monkeypatch.delenv("INN_API_KEY", raising=False)
    (inn_root / ".env").write_text("INN_API_KEY=secret-from-file\n", encoding="utf-8")
    load_dotenv(inn_root)
    assert os.environ["INN_API_KEY"] == "secret-from-file"


def test_run_tool_shelve_refusal(inn_root: Path):
    result = run_tool(
        "shelve",
        {
            "room_id": "study",
            "content": "x",
            "adopting_words": "That's lovely!",
        },
        root=inn_root,
    )
    assert result["ok"] is False
    assert "enthusiasm" in result["refusal"].lower() or "adoption" in result["refusal"].lower()


def test_run_tool_set_room(inn_root: Path):
    result = run_tool("set_room", {"room_id": "desk"}, root=inn_root)
    assert result["ok"] is True
    assert result["current_room"] == "desk"


def test_run_guest_turn_mocked_api(inn_root: Path):
    from inn.host import open_stay_transcript

    fake = {
        "choices": [
            {
                "message": {
                    "role": "assistant",
                    "content": "What brings you to the lake?",
                }
            }
        ]
    }
    transcript = open_stay_transcript(root=inn_root, model="mock", api_base="http://x")
    with patch("inn.cli_host.chat_completion", return_value=fake):
        text, history = run_guest_turn(
            "hello",
            root=inn_root,
            api_key="test",
            api_base="http://example.invalid/v1",
            model="mock",
            history=[],
            transcript=transcript,
        )
    assert "lake" in text.lower() or "brings" in text.lower()
    assert len(history) == 2
    assert history[0]["role"] == "user"
    envelopes = list((inn_root / "logs" / "host").glob("*-turn.json"))
    assert len(envelopes) == 1
    body = transcript.read_text(encoding="utf-8")
    assert "hello" in body
    assert "lake" in body.lower() or "brings" in body.lower()
    assert "pair_root_id" in body


def test_stay_transcript_helpers(inn_root: Path):
    from inn.host import append_stay_turn, close_stay_transcript, open_stay_transcript

    path = open_stay_transcript(root=inn_root, model="m", api_base="b")
    append_stay_turn(path, writer="hi", guest="hello", pair_root_id=7)
    close_stay_transcript(path, note="done")
    text = path.read_text(encoding="utf-8")
    assert "**Writer:**" in text and "hi" in text
    assert "Stay ended" in text
