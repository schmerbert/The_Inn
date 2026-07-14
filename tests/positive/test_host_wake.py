"""Positive — host wake core (no live API)."""

from __future__ import annotations

import json
from pathlib import Path

from inn import session
from inn.host import guest_system_prompt, ingest_turn, new_envelope, wake, write_turn_envelope


def test_wake_returns_packet_with_tool_catalog(inn_root: Path):
    packet = wake(inn_root)
    assert packet["posture"] == "guest"
    assert "shelve" in packet["tools"]
    assert "read_ground" in packet["tools"]
    assert "exhale" in packet["tools"]
    assert "adopt" not in json.dumps(packet["tools"])


def test_read_ground_lookup(inn_root: Path):
    from inn.host import read_ground

    (inn_root / "study" / "canon.md").write_text("Lake mist.\n", encoding="utf-8")
    ok = read_ground("study/canon.md", root=inn_root)
    assert ok["ok"] is True
    assert "Lake mist" in ok["text"]
    bad = read_ground("desk/secret.md", root=inn_root)
    assert bad["ok"] is False


def test_ingest_turn_sets_last_pair_root(inn_root: Path):
    pair_id = ingest_turn("What brings you?", "The lake excerpt.", root=inn_root)
    state = session.load(inn_root)
    assert state.last_pair_root_id == pair_id
    assert pair_id > 0


def test_guest_system_prompt_names_homework(inn_root: Path):
    packet = wake(inn_root)
    text = guest_system_prompt(packet)
    assert "homework" in text.lower()
    assert "read_ground" in text
    assert "Shelving" in text or "shelving" in text.lower()


def test_write_turn_envelope(inn_root: Path):
    env = new_envelope(fit_ms=12.5)
    env["pair_root_id"] = 1
    path = write_turn_envelope(env, root=inn_root)
    assert path.exists()
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["kind"] == "host_turn"
    assert data["fit_ms"] == 12.5
