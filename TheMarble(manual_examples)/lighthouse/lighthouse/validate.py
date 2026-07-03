"""Arrival validator — the check cabin earned.

Every file the arrival documents point at must exist. An arrival seat
containing false ground is the marble failing its own law at the door.
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ARRIVAL_DOCS = ("ARRIVAL.md", "MANIFEST.md", "HANDOFF.md", "CLAUDE.md")

# Every verb the console has. cli.py asserts its parser matches this list,
# so a new command can't be added without the door check learning it.
COMMANDS = ("fix", "dr", "supersede", "exhale", "check", "status", "audit",
            "validate", "breathe", "sit", "keep", "handover")

# Backtick-quoted repo-relative paths like `lighthouse/fix.py` or `tests/test_hostile.py`.
_REF = re.compile(r"`([A-Za-z0-9_./\\-]+\.(?:md|py|sql|txt|json))`")

# Console verbs named in prose, like `python -m lighthouse supersede`.
# Earned 2026-07-01: the handoff instructed keepers to use a verb that
# didn't exist yet. Every named pen must hang on the wall.
_VERB = re.compile(r"python -m lighthouse ([a-z]+)\b")


def check(root: Path | None = None) -> list[str]:
    root = root or ROOT
    problems: list[str] = []
    for doc_name in ARRIVAL_DOCS:
        doc = root / doc_name
        if not doc.exists():
            problems.append(f"{doc_name}: arrival document missing entirely")
            continue
        text = doc.read_text(encoding="utf-8")
        for match in _REF.finditer(text):
            ref = match.group(1)
            if not (root / ref).exists():
                problems.append(f"{doc_name}: points to `{ref}` which does not exist")
        for match in _VERB.finditer(text):
            verb = match.group(1)
            if verb not in COMMANDS and verb != "lighthouse":
                problems.append(
                    f"{doc_name}: names console verb '{verb}' which is not on the wall"
                    f" (have: {', '.join(COMMANDS)})"
                )
    return problems
