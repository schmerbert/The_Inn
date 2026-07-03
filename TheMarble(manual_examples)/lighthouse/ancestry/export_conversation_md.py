#!/usr/bin/env python3
"""Render ancestry/conversation.jsonl to conversation.md (human-readable)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
JSONL = ROOT / "conversation.jsonl"
OUT = ROOT / "conversation.md"


def _tool_summary(block: dict) -> str:
    name = block.get("name", "?")
    inp = block.get("input") or {}
    if name in ("Read", "Write", "StrReplace", "Delete", "Edit", "NotebookEdit"):
        path = inp.get("file_path") or inp.get("path", "")
        return f"{name}: {path}"
    if name == "Bash":
        cmd = (inp.get("command") or "")[:120]
        full = inp.get("command") or ""
        return f"Bash: {cmd}{'...' if len(full) > 120 else ''}"
    if name == "Grep":
        return f"Grep: {inp.get('pattern', '')!r} in {inp.get('path', '.')}"
    if name == "Glob":
        return f"Glob: {inp.get('glob_pattern', '')}"
    return f"{name}: {json.dumps(inp, ensure_ascii=False)[:100]}"


def _content_blocks(content: object) -> tuple[list[str], list[str]]:
    texts: list[str] = []
    tools: list[str] = []
    if isinstance(content, str):
        if content.strip():
            texts.append(content.strip())
        return texts, tools
    if not isinstance(content, list):
        return texts, tools
    for block in content:
        if not isinstance(block, dict):
            continue
        kind = block.get("type")
        if kind == "text":
            text = (block.get("text") or "").strip()
            if text:
                texts.append(text)
        elif kind == "tool_use":
            tools.append(_tool_summary(block))
        elif kind == "tool_result":
            preview = (block.get("content") or "")[:80].replace("\n", " ")
            if preview:
                tools.append(f"tool_result: {preview}...")
    return texts, tools


def _is_user_prompt(content: object) -> bool:
    if isinstance(content, str):
        return bool(content.strip())
    if isinstance(content, list):
        return any(
            isinstance(b, dict) and b.get("type") == "text"
            for b in content
        )
    return False


def main() -> int:
    if not JSONL.exists():
        print(f"missing {JSONL}", file=sys.stderr)
        return 1

    lines = JSONL.read_text(encoding="utf-8").splitlines()
    parts: list[str] = [
        "# Lighthouse — conversation ancestry (readable export)",
        "",
        "Generated from `conversation.jsonl` by `export_conversation_md.py`.",
        "The JSONL file is the canonical log; this markdown is for reading.",
        "",
        "Claude Desktop export: user prompts and assistant replies are preserved;",
        "attachment deltas and tool-result-only turns are omitted from this view.",
        "File writes in tool calls point at paths; the marble on disk is ground truth.",
        "",
        f"**Records:** {len(lines)} jsonl lines",
        "",
        "---",
        "",
    ]

    turn = 0
    for line in lines:
        if not line.strip():
            continue
        row = json.loads(line)
        row_type = row.get("type")
        msg = row.get("message") or {}

        if row_type == "queue-operation" and row.get("operation") == "enqueue":
            content = (row.get("content") or "").strip()
            if content:
                turn += 1
                parts.append(f"## Turn {turn} — user")
                parts.append("")
                parts.append(content)
                parts.append("")
                parts.append("---")
                parts.append("")
            continue

        if row_type != "user" and row_type != "assistant":
            continue

        role = msg.get("role") or row_type
        content = msg.get("content")
        if role == "user" and not _is_user_prompt(content):
            continue

        texts, tools = _content_blocks(content)
        if role == "assistant" and not texts and not tools:
            continue

        turn += 1
        parts.append(f"## Turn {turn} — {role}")
        parts.append("")

        if role == "user":
            for t in texts:
                parts.append(t)
                parts.append("")
        else:
            for t in texts:
                parts.append(t)
                parts.append("")
            if tools:
                parts.append("### Tool calls this turn")
                parts.append("")
                for t in tools:
                    parts.append(f"- {t}")
                parts.append("")

        parts.append("---")
        parts.append("")

    OUT.write_text("\n".join(parts), encoding="utf-8")
    print(f"wrote {OUT} ({len(parts)} lines)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
