#!/usr/bin/env python3
"""Redact machine-local details from logs/ before publish.

Ancestry: lighthouse/ancestry/sanitize_ancestry.py (same law, second marble).
Originals are archived untouched in logs/.source/ (gitignored, local only) —
nothing is deleted; the published copy is the sanitized projection.
"""

from __future__ import annotations

import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LOGS = ROOT / "logs"
SOURCE = LOGS / ".source"

REPLACEMENTS: list[tuple[re.Pattern[str], str]] = [
    # Claude project-cache encodings (leak username + folder layout)
    (re.compile(r"C--Users-forre[^\s\"'`\\/]*", re.IGNORECASE), "<claude-project>"),
    (re.compile(r"[Cc]:[/\\]Users[/\\]forre[/\\]\.claude[/\\]projects[/\\][^\s\"'`]*", re.IGNORECASE), "<claude-project>"),
    # Home paths -> ~ (keeps them readable and locally reconstructable)
    (re.compile(r"[Cc]:[/\\]Users[/\\]forre", re.IGNORECASE), "~"),
    (re.compile(r"C:\\\\Users\\\\forre", re.IGNORECASE), "~"),
    # ls owner/gid columns
    (re.compile(r"\b1 forre 197610\b"), "1 <user> <gid>"),
    (re.compile(r"\bforre 197610\b"), "<user> <gid>"),
    (re.compile(r"\b197610\b"), "<gid>"),
    (re.compile(r"\bforre\b"), "<user>"),
]


def sanitize(text: str) -> str:
    for pattern, repl in REPLACEMENTS:
        text = pattern.sub(repl, text)
    return text


def main() -> int:
    SOURCE.mkdir(exist_ok=True)
    changed = 0
    for md in sorted(LOGS.rglob("*.md")):
        if SOURCE in md.parents:
            continue
        original = md.read_text(encoding="utf-8")
        clean = sanitize(original)
        if clean != original:
            backup = SOURCE / md.relative_to(LOGS)
            backup.parent.mkdir(parents=True, exist_ok=True)
            if not backup.exists():
                shutil.copy2(md, backup)
            md.write_text(clean, encoding="utf-8")
            changed += 1
            print(f"sanitized {md.relative_to(ROOT)}")
    print(f"{changed} file(s) changed; originals in logs/.source/ (gitignored)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
