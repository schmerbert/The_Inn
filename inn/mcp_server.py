# mcp_server — thin MCP stdio surface for The Inn (Layer 5).
#
# Stores: nothing itself (delegates to host/breath/shelve/session)
# Refuses: unknown tools; shelve refusals returned as structured content
# Returns: MCP tool results over stdout
# Test: tests/positive/test_mcp_tools.py
#
# Run: python -m inn.mcp_server
# Wire: see HOST.md

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from inn import breath, forest, session
from inn.errors import BreathRefusal, ShelvingRefusal
from inn.host import ingest_turn, read_ground, wake
from inn.paths import repo_root
from inn.shelve import shelve


def _root() -> Path:
    import os

    if os.environ.get("INN_ROOT"):
        return Path(os.environ["INN_ROOT"]).resolve()
    return repo_root()


TOOLS = [
    {
        "name": "inhale",
        "description": "Wake / arrival packet. Call first. Homework — ids/paths only.",
        "inputSchema": {"type": "object", "properties": {}},
    },
    {
        "name": "read_ground",
        "description": "Lookup — open ground file by path. Not Shelving.",
        "inputSchema": {
            "type": "object",
            "properties": {"path": {"type": "string"}},
            "required": ["path"],
        },
    },
    {
        "name": "shelve",
        "description": "Shelving crossing to study or manuscript ground.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "room_id": {"type": "string"},
                "content": {"type": "string"},
                "adopting_words": {"type": "string"},
                "source_verbatim": {"type": "string"},
            },
            "required": ["room_id", "content", "adopting_words"],
        },
    },
    {
        "name": "set_room",
        "description": "Set current room for next inhale.",
        "inputSchema": {
            "type": "object",
            "properties": {"room_id": {"type": "string"}},
            "required": ["room_id"],
        },
    },
    {
        "name": "record_pair",
        "description": "Insert conversation pair into woods (custody).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "guest_words": {"type": "string"},
                "innkeeper_words": {"type": "string"},
            },
            "required": ["guest_words"],
        },
    },
    {
        "name": "refuse_invention",
        "description": "Invented fact → open question bucket.",
        "inputSchema": {
            "type": "object",
            "properties": {"detail": {"type": "string"}},
            "required": ["detail"],
        },
    },
    {
        "name": "exhale",
        "description": "Seat check before end of stay.",
        "inputSchema": {"type": "object", "properties": {}},
    },
]


def call_tool(name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    root = _root()
    if name == "inhale":
        return wake(root)
    if name == "read_ground":
        return read_ground(arguments.get("path") or "", root=root)
    if name == "shelve":
        try:
            rid = shelve(
                arguments["room_id"],
                arguments["content"],
                arguments["adopting_words"],
                source_verbatim=arguments.get("source_verbatim"),
                root=root,
            )
            return {"ok": True, "adoption_record_id": rid}
        except ShelvingRefusal as exc:
            return {"ok": False, "refusal": str(exc)}
    if name == "set_room":
        state = session.set_room(arguments["room_id"], root)
        return {"ok": True, "current_room": state.current_room}
    if name == "record_pair":
        pid = ingest_turn(
            arguments["guest_words"],
            arguments.get("innkeeper_words"),
            root=root,
        )
        return {"ok": True, "pair_root_id": pid}
    if name == "refuse_invention":
        forest.init_db(root)
        with forest.connect(root) as conn:
            state = session.load(root)
            origin = state.last_pair_root_id
            if origin is None:
                origin = forest.insert_pair_root(
                    conn, signature="model", body="mcp refuse_invention"
                )
            q_id = forest.refuse_ground_invention(
                conn, detail=arguments["detail"], pair_root_id=origin
            )
            conn.commit()
        return {"ok": True, "question_id": q_id}
    if name == "exhale":
        try:
            return {"ok": True, **breath.exhale(root)}
        except BreathRefusal as exc:
            return {"ok": False, "clear": False, "held": [str(exc)]}
    return {"ok": False, "refusal": f"unknown tool {name!r}"}


def _reply(msg_id: Any, result: Any) -> None:
    sys.stdout.write(
        json.dumps({"jsonrpc": "2.0", "id": msg_id, "result": result}) + "\n"
    )
    sys.stdout.flush()


def _error(msg_id: Any, code: int, message: str) -> None:
    sys.stdout.write(
        json.dumps(
            {
                "jsonrpc": "2.0",
                "id": msg_id,
                "error": {"code": code, "message": message},
            }
        )
        + "\n"
    )
    sys.stdout.flush()


def handle(message: dict[str, Any]) -> None:
    method = message.get("method")
    msg_id = message.get("id")
    params = message.get("params") or {}

    # Notifications (no id) — ignore politely
    if msg_id is None and method:
        return

    if method == "initialize":
        _reply(
            msg_id,
            {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "the-inn", "version": "0.5.0"},
            },
        )
        return
    if method == "notifications/initialized":
        return
    if method == "tools/list":
        _reply(msg_id, {"tools": TOOLS})
        return
    if method == "tools/call":
        name = params.get("name")
        arguments = params.get("arguments") or {}
        try:
            payload = call_tool(name, arguments)
            _reply(
                msg_id,
                {
                    "content": [
                        {"type": "text", "text": json.dumps(payload, indent=2)}
                    ]
                },
            )
        except Exception as exc:
            _reply(
                msg_id,
                {
                    "isError": True,
                    "content": [{"type": "text", "text": str(exc)}],
                },
            )
        return
    if method == "ping":
        _reply(msg_id, {})
        return
    _error(msg_id, -32601, f"Method not found: {method}")


def main() -> int:
    from inn.cli_host import load_dotenv

    load_dotenv(_root())
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            message = json.loads(line)
        except json.JSONDecodeError:
            continue
        handle(message)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
