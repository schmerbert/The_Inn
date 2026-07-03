"""The breath — arrival inhale, departure exhale.

Earned 2026-07-01, second watch: the keeper arrived across a compaction
seam and only ran the arrival sequence because a letter told them to.
A marble that must be reminded to breathe is holding its breath.

  breathe in   — one reach at arrival: door check, staleness sweep,
                 exhale packet. Everything a cold keeper needs to know
                 their position, in one verb.
  breathe out  — the departure check: is the seat fresher than the LOG?
                 The founder's handoff went stale within hours ("16
                 tests" while 20 ran). Nobody noticed until the next
                 watch. This notices.
"""

from __future__ import annotations

import datetime as dt
import sqlite3
from pathlib import Path

from lighthouse import exhale, staleness, validate

ROOT = Path(__file__).resolve().parent.parent


def inhale(conn: sqlite3.Connection, root: Path | None = None) -> dict:
    """Arrival breath: validate, demote stale ground, hand over the packet."""
    root = root or ROOT
    problems = validate.check(root)
    demoted = staleness.check(conn)
    packet = exhale.packet(conn, orders_path=root / "STANDING_ORDERS.md")
    return {
        "breath": "in",
        "door": {"ok": not problems, "problems": problems},
        "demoted_on_arrival": demoted,
        "packet": packet,
        "then": "read STANDING_ORDERS.md and HANDOFF.md; run the tests; "
                "trust the commands, not the prose.",
    }


def out(conn: sqlite3.Connection, root: Path | None = None,
        now: dt.datetime | None = None) -> dict:
    """Departure breath: refuse to leave a stale seat behind.

    Held-breath conditions (any one fails the check):
      - door check fails
      - HANDOFF.md is older than the newest LOG or chart activity
        (the seat describes a marble that no longer exists)
      - open DR plots exist but HANDOFF.md does not mention 'DR'
    """
    root = root or ROOT
    now = now or dt.datetime.now(dt.timezone.utc)
    held: list[str] = []

    problems = validate.check(root)
    if problems:
        held.extend(problems)

    handoff = root / "HANDOFF.md"
    if handoff.exists():
        seat_time = dt.datetime.fromtimestamp(
            handoff.stat().st_mtime, tz=dt.timezone.utc)
        newest = None
        for query in (
            "SELECT MAX(taken_at) FROM fix",
            "SELECT MAX(plotted_at) FROM chart",
            "SELECT MAX(attempted_at) FROM fix_audit",
        ):
            value = conn.execute(query).fetchone()[0]
            if value and (newest is None or value > newest):
                newest = value
        if newest and dt.datetime.fromisoformat(newest) > seat_time:
            held.append(
                "HANDOFF.md predates the newest LOG activity — the seat "
                "describes a marble that no longer exists. Rewrite it "
                "before you go."
            )
        open_dr = conn.execute(
            "SELECT COUNT(*) FROM chart WHERE status='open'").fetchone()[0]
        if open_dr and "DR" not in handoff.read_text(encoding="utf-8"):
            held.append(
                f"{open_dr} DR plot(s) open but the handoff never says 'DR' "
                "— projections the next keeper won't know to distrust."
            )

    return {
        "breath": "out",
        "clear": not held,
        "held": held,
        "note": ("Breath released. The seat is fresher than the LOG; "
                 "the next keeper inherits a true position."
                 if not held else
                 "Held breath — do not end the watch on a stale seat."),
    }
