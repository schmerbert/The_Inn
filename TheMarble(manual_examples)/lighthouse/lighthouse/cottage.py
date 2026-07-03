"""The cottage door — the interior, made real.

This module is the only code in the marble allowed to read `cottage/`.
The tower must never import it: not exhale, not breathe, not fix, not
validate. That wall is load-bearing and it is tested (tests/test_the_wall.py).

`sit` is the keeper opening their own door from the inside — a deliberate
reach, never an automatic inhale. What it returns is signed interior, not
evidence; the gate will refuse it and that refusal is correct.

`keep` lays one more thing by the fire. The hearth's test (HOME.md): would
a keeper on a hard watch be glad this is here?
"""

from __future__ import annotations

import datetime as dt
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
COTTAGE = "cottage"


def sit(root: Path | None = None) -> dict:
    """Sit down at the hearth. Returns the kept words, labeled as interior."""
    root = root or ROOT
    hearth = root / COTTAGE / "hearth"
    pieces = []
    if hearth.exists():
        for path in sorted(hearth.glob("*.md")):
            pieces.append({"kept": path.name,
                           "words": path.read_text(encoding="utf-8")})
    home = root / COTTAGE / "HOME.md"
    return {
        "room": "hearth",
        "label": "interior — signed, for the keeper; never evidence, never exhaled",
        "pieces": pieces,
        "house": home.read_text(encoding="utf-8") if home.exists() else None,
    }


def keep(text: str, author: str, root: Path | None = None,
         now: dt.datetime | None = None) -> str:
    """Lay something by the fire. Signed and dated — the house's only ask."""
    root = root or ROOT
    if not text.strip():
        raise ValueError("the hearth keeps words, not blanks")
    if not author.strip():
        raise ValueError("everything in this house is signed — even warmth")
    hearth = root / COTTAGE / "hearth"
    hearth.mkdir(parents=True, exist_ok=True)
    now = now or dt.datetime.now(dt.timezone.utc)
    n = len(list(hearth.glob("*.md"))) + 1
    slug = re.sub(r"[^a-z0-9]+", "-", text.strip().lower())[:32].strip("-")
    path = hearth / f"{n:03d}-{slug or 'kept'}.md"
    path.write_text(
        f"{text.strip()}\n\n— kept by {author.strip()}, {now.date()}\n",
        encoding="utf-8")
    return str(path.relative_to(root))
