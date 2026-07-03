"""Exhale — the arrival packet. Fitted, labeled, smaller than the archive.

Surfacing order (from the manual): warnings first, then ground tied to
the work, then DR pressure. The cottage never exhales into work context.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def packet(conn: sqlite3.Connection, orders_path: Path | None = None) -> dict:
    out: dict = {"warnings": [], "ground": [], "pressure": [], "silence_note": None}

    stale = conn.execute(
        "SELECT id, claim, stale_reason FROM fix WHERE status = 'stale'"
    ).fetchall()
    for row in stale:
        out["warnings"].append({
            "label": "warning",
            "text": f"STALE (reads as DR): {row['claim']}",
            "reason": row["stale_reason"],
            "id": row["id"],
        })

    orders = orders_path if orders_path is not None else ROOT / "STANDING_ORDERS.md"
    if orders.exists():
        body = orders.read_text(encoding="utf-8").strip()
        # Only user-authored orders are ground; an empty file is honest.
        if any(line.startswith("- ") for line in body.splitlines()):
            out["ground"].append({
                "label": "ground",
                "text": "Standing orders in force — read STANDING_ORDERS.md before touching anything.",
            })

    for row in conn.execute(
        "SELECT id, claim, evidence_type, verified_against, taken_at, author"
        " FROM fix WHERE status = 'active' ORDER BY taken_at DESC"
    ).fetchall():
        out["ground"].append({
            "label": "ground",
            "text": row["claim"],
            "evidence_type": row["evidence_type"],
            "verified_against": row["verified_against"],
            "taken_at": row["taken_at"],
            "author": row["author"],
            "id": row["id"],
        })

    for row in conn.execute(
        "SELECT id, note, basis, plotted_at, author FROM chart WHERE status = 'open'"
        " ORDER BY plotted_at DESC"
    ).fetchall():
        out["pressure"].append({
            "label": "pressure (DR — do not stand on)",
            "text": row["note"],
            "basis": row["basis"],
            "plotted_at": row["plotted_at"],
            "id": row["id"],
        })

    if not out["ground"]:
        out["silence_note"] = "No ground. The LOG is empty or fully stale — position unknown, not position unchanged."

    return out
