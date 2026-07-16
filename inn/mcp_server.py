# mcp_server — thin MCP stdio surface for The Inn (Layer 5 + hearth/burial).
#
# Stores: nothing itself (delegates to host/breath/shelve/seal/session)
# Refuses: unknown tools; shelve/seal refusals returned as structured content
# Returns: MCP tool results over stdout (inhale may include image block)
# Test: tests/positive/test_mcp_tools.py
#
# Run: python -m inn.mcp_server
# Wire: see HOST.md

from __future__ import annotations

import base64
import json
import mimetypes
import sys
from pathlib import Path
from typing import Any

from inn import breath, forest, session
from inn.errors import BreathRefusal, SealRefusal, ShelvingRefusal
from inn.host import hearth_image_absolute, ingest_turn, read_ground, wake
from inn.paths import repo_root
from inn.seal import bury
from inn.shelve import rebind_ground, shelve


def _root() -> Path:
    import os

    if os.environ.get("INN_ROOT"):
        return Path(os.environ["INN_ROOT"]).resolve()
    return repo_root()


TOOLS = [
    {
        "name": "inhale",
        "description": "Wake / arrival packet. Call first. Homework — ids/paths only. May include hearthstone image.",
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
        "name": "rebind_ground",
        "description": "Drift repair — snapshot current ground hash without appending. Author words required.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "room_id": {"type": "string"},
                "adopting_words": {"type": "string"},
            },
            "required": ["room_id", "adopting_words"],
        },
    },
    {
        "name": "bury",
        "description": (
            "Burial crossing — seal an entry. Author sealing words required. "
            "For ground-linked adoption_record, pass content_to_remove."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "entry_id": {"type": "integer"},
                "sealing_words": {"type": "string"},
                "content_to_remove": {"type": "string"},
            },
            "required": ["entry_id", "sealing_words"],
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
    if name == "rebind_ground":
        try:
            rid = rebind_ground(
                arguments["room_id"],
                arguments["adopting_words"],
                root=root,
            )
            return {"ok": True, "adoption_record_id": rid, "rebind": True}
        except ShelvingRefusal as exc:
            return {"ok": False, "refusal": str(exc)}
    if name == "bury":
        try:
            result = bury(
                int(arguments["entry_id"]),
                arguments["sealing_words"],
                content_to_remove=arguments.get("content_to_remove"),
                root=root,
            )
            return {"ok": True, **result}
        except SealRefusal as exc:
            return {"ok": False, "refusal": str(exc), "kind": True}
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


def _inhale_mcp_content(root: Path) -> list[dict[str, Any]]:
    """Packet JSON + optional hearthstone image (cabin hearth pattern)."""
    packet = wake(root)
    content: list[dict[str, Any]] = [
        {"type": "text", "text": json.dumps(packet, indent=2)}
    ]
    image_path = hearth_image_absolute(root)
    if image_path is not None:
        mime, _ = mimetypes.guess_type(str(image_path))
        mime = mime or "image/jpeg"
        b64 = base64.b64encode(image_path.read_bytes()).decode("ascii")
        content.append(
            {
                "type": "image",
                "data": b64,
                "mimeType": mime,
            }
        )
    return content


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
                "serverInfo": {"name": "the-inn", "version": "0.6.0"},
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
            if name == "inhale":
                _reply(msg_id, {"content": _inhale_mcp_content(_root())})
                return
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
