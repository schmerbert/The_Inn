"""The chart table — dead reckoning welcome, labeled as such.

No gate here on purpose: DR must be cheap to write, or keepers will be
tempted to force projections through the fix gate just to store them.
The safe path stays small enough to use.
"""

from __future__ import annotations

import sqlite3
import uuid
from datetime import datetime, timezone


def plot(conn: sqlite3.Connection, note: str, author: str, basis: str | None = None) -> str:
    note = (note or "").strip()
    if not note:
        raise ValueError("empty DR plot")
    dr_id = f"dr-{uuid.uuid4().hex[:10]}"
    conn.execute(
        "INSERT INTO chart (id, note, basis, plotted_at, author) VALUES (?, ?, ?, ?, ?)",
        (dr_id, note, (basis or "").strip() or None,
         datetime.now(timezone.utc).isoformat(timespec="seconds"), (author or "keeper").strip()),
    )
    conn.commit()
    return dr_id


def supersede(conn: sqlite3.Connection, dr_id: str) -> None:
    conn.execute("UPDATE chart SET status = 'superseded' WHERE id = ?", (dr_id,))
    conn.commit()
