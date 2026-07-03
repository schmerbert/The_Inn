"""Staleness — the channel where reality re-enters the LOG.

Absence of a fresh fix must read as position unknown, never position
unchanged. A stale fix is not deleted: it is demoted to DR authority
and keeps its history. Demotion is loud, reversible only by a new fix.
"""

from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path

DEFAULT_MAX_AGE_DAYS = 14


def check(conn: sqlite3.Connection, max_age_days: int = DEFAULT_MAX_AGE_DAYS,
          now: datetime | None = None) -> list[dict]:
    """Demote fixes whose sighting is old or whose verified_against path is gone."""
    now = now or datetime.now(timezone.utc)
    cutoff = now - timedelta(days=max_age_days)
    demoted: list[dict] = []

    for row in conn.execute("SELECT * FROM fix WHERE status = 'active'").fetchall():
        reason = None
        taken = datetime.fromisoformat(row["taken_at"])
        if taken < cutoff:
            reason = f"sighting older than {max_age_days} days — re-verify before standing on it"
        else:
            # If the fix was verified against a filesystem path that no longer
            # exists, the ground it stood on has moved.
            va = row["verified_against"]
            if va and (va.startswith((".", "/", "\\")) or ":" in va[:3]) and not Path(va).exists():
                reason = f"verified_against path no longer exists: {va}"

        if reason:
            conn.execute(
                "UPDATE fix SET status = 'stale', stale_reason = ? WHERE id = ?",
                (reason, row["id"]),
            )
            demoted.append({"id": row["id"], "claim": row["claim"], "reason": reason})

    conn.commit()
    return demoted
