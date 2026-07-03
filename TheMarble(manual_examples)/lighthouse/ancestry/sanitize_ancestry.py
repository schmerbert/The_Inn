#!/usr/bin/env python3
"""Redact machine-local and third-party personal details from ancestry logs."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "conversation.source.jsonl"
JSONL = ROOT / "conversation.jsonl"

# Machine-local paths -> repo-relative
_PATH_REPLACEMENTS: list[tuple[re.Pattern[str], str]] = [
    (
        re.compile(
            r"marble_starter[\\/]+projects[\\/]+c-Users-forre-OneDrive-Desktop-AI-marble-starter",
            re.IGNORECASE,
        ),
        "<cursor-project>",
    ),
    (
        re.compile(r"c-Users-forre-OneDrive-Desktop-AI-marble-starter", re.IGNORECASE),
        "<cursor-project>",
    ),
    (
        re.compile(r"C--Users-forre-OneDrive-Desktop-AI-marble-starter", re.IGNORECASE),
        "<claude-project>",
    ),
    (
        re.compile(
            r"[Cc]:[/\\]Users[/\\]forre[/\\]OneDrive[/\\]Desktop[/\\]AI[/\\]marble_starter",
            re.IGNORECASE,
        ),
        "marble_starter",
    ),
    (
        re.compile(r"[Cc]:[/\\]Users[/\\]forre[/\\][^\"\\s]*", re.IGNORECASE),
        "marble_starter",
    ),
    (
        re.compile(
            r"C:\\\\Users\\\\forre\\\\OneDrive\\\\Desktop\\\\AI\\\\marble_starter",
            re.IGNORECASE,
        ),
        "marble_starter",
    ),
    (
        re.compile(r"C:\\\\Users\\\\forre\\\\[^\"\\\\]*", re.IGNORECASE),
        "marble_starter",
    ),
    (
        re.compile(r"[Cc]:[/\\]Users[/\\]forre[/\\]AppData[/\\]Local[/\\]Temp[/\\][^\"\\s]+", re.IGNORECASE),
        "<temp>",
    ),
    (
        re.compile(
            r"C:\\\\Users\\\\forre\\\\AppData\\\\Local\\\\Temp\\\\[^\"\\\\]+",
            re.IGNORECASE,
        ),
        "<temp>",
    ),
    (
        re.compile(
            r"[Cc]:[/\\]Users[/\\]forre[/\\]\.cursor[/\\]projects[/\\][^\"\\]+",
            re.IGNORECASE,
        ),
        "<cursor-project>",
    ),
    (
        re.compile(
            r"C:\\\\Users\\\\forre\\\\.cursor\\\\projects\\\\[^\"\\\\]+",
            re.IGNORECASE,
        ),
        "<cursor-project>",
    ),
    (
        re.compile(
            r"[Cc]:[/\\]Users[/\\]forre[/\\]\.claude[/\\]projects[/\\][^\"\\]+",
            re.IGNORECASE,
        ),
        "<claude-project>",
    ),
    (
        re.compile(
            r"C:\\\\Users\\\\forre\\\\.claude\\\\projects\\\\[^\"\\\\]+",
            re.IGNORECASE,
        ),
        "<claude-project>",
    ),
]

# Tower specimen friction — names/dates from a real-use marble review in chat
_TEXT_REPLACEMENTS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"\bGrey's\b"), "Roster contact's"),
    (re.compile(r"\bGrey\b"), "Roster contact"),
    (re.compile(r"brother's Japan trip", re.IGNORECASE), "hedged family trip"),
    (re.compile(r"Japan trip", re.IGNORECASE), "hedged trip"),
    (re.compile(r"\bNov 13\b"), "[overlap date]"),
    (re.compile(r"\bYour birthday\b"), "A logged birthday"),
    (re.compile(r"Your birthday and Roster contact's trip", re.IGNORECASE), "A birthday and hedged trip"),
    (re.compile(r"\b1 forre 197610\b"), "1 <user> <gid>"),
    (re.compile(r"<user> 197610\b"), "<user> <gid>"),
    (
        re.compile(
            r"<image_files>.*?</image_files>",
            re.DOTALL | re.IGNORECASE,
        ),
        "[image attachment omitted]",
    ),
    (
        re.compile(
            r"The following images were provided by the user and saved to the workspace.*?\n",
            re.DOTALL | re.IGNORECASE,
        ),
        "",
    ),
    (re.compile(r"\[Image\]\s*"), ""),
]


def sanitize_text(text: str) -> str:
    out = text
    for pattern, repl in _PATH_REPLACEMENTS:
        out = pattern.sub(repl, out)
    for pattern, repl in _TEXT_REPLACEMENTS:
        out = pattern.sub(repl, out)
    return out


def sanitize_obj(obj: object) -> object:
    if isinstance(obj, str):
        return sanitize_text(obj)
    if isinstance(obj, list):
        return [sanitize_obj(x) for x in obj]
    if isinstance(obj, dict):
        return {k: sanitize_obj(v) for k, v in obj.items()}
    return obj


def main() -> int:
    src = SOURCE if SOURCE.exists() else JSONL
    if not src.exists():
        print("no conversation jsonl found", file=sys.stderr)
        return 1

    if src == JSONL and not SOURCE.exists():
        SOURCE.write_bytes(JSONL.read_bytes())
        print(f"archived original -> {SOURCE.name}")

    raw_lines = src.read_text(encoding="utf-8").splitlines()
    clean_lines: list[str] = []
    for line in raw_lines:
        if not line.strip():
            continue
        row = json.loads(line)
        clean_lines.append(json.dumps(sanitize_obj(row), ensure_ascii=False))

    JSONL.write_text("\n".join(clean_lines) + "\n", encoding="utf-8")
    print(f"sanitized {len(clean_lines)} turns -> {JSONL.name}")

    import export_conversation_md

    export_conversation_md.main()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
