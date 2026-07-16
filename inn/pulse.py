# pulse — faun signed between-stay notes (thin slice; no mycelium engine).
#
# Stores: woods entry bucket=note, signature=faun, meta kind=faun_pulse + voice + consumed_at
# Refuses: unsigned; empty body; meal-sized body (>gesture); mid-session inject (callers);
#          resurfacing after one inhale (decay)
# Returns: plant → entry id; fit_unread → snippet or None; consume marks meta.consumed_at
# Test: tests/hostile/test_pulse_decay.py, tests/positive/test_pulse_plant.py
#
# TRAILHEAD — schema faun_note deferred; note+meta until next woods rebuild.
# Sentinel FAUN_PULSE: in body. Voice label faun only this slice (not mycelium).

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from inn import forest
from inn.errors import ForestRefusal
from inn.paths import repo_root

SENTINEL = "FAUN_PULSE:"
SIGNATURE = "faun"
# Gesture ceiling — nod/gesture, never a meal (MAP faun friction).
_MAX_CHARS = 600


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _meta(row: sqlite3.Row | dict[str, Any]) -> dict[str, Any]:
    raw = row["meta_json"] if not isinstance(row, dict) else row.get("meta_json", "{}")
    if isinstance(raw, dict):
        return raw
    return json.loads(raw or "{}")


def plant(
    body: str,
    *,
    voice: str = "faun",
    signature: str = SIGNATURE,
    root: Path | None = None,
    conn: sqlite3.Connection | None = None,
) -> int:
    """Insert one signed pulse for the next wake. Not ground."""
    root = root or repo_root()
    text = (body or "").strip()
    if not signature or not str(signature).strip():
        raise ForestRefusal("unsigned pulse refused")
    if not text:
        raise ForestRefusal("empty pulse refused")
    if not text.startswith(SENTINEL):
        text = f"{SENTINEL}\n{text}"
    if len(text) > _MAX_CHARS:
        raise ForestRefusal("pulse too large — gesture only, not a meal")

    meta = {
        "kind": "faun_pulse",
        "voice": voice,
        "consumed_at": None,
        "planted_at": _now(),
    }

    def _cross(db: sqlite3.Connection) -> int:
        return forest.insert(
            db,
            forest="home",
            bucket="note",
            signature=signature,
            authority="inference",
            body=text,
            meta=meta,
            is_pair_root=True,
        )

    if conn is not None:
        return _cross(conn)

    forest.init_db(root)
    with forest.connect(root) as db:
        eid = _cross(db)
        db.commit()
        return eid


def plant_stay_gesture(
    *,
    root: Path | None = None,
    current_room: str = "",
    warning_count: int = 0,
    ground_paths: list[str] | None = None,
) -> int:
    """Deterministic dusk gesture from stay facts — no LLM required."""
    paths = ground_paths or []
    lines = [
        SENTINEL,
        f"—f room was {current_room or '(unset)'}",
        f"—f warnings on last fit: {warning_count}",
    ]
    if paths:
        lines.append(f"—f ground paths: {', '.join(paths[:6])}")
    lines.append("—f not ground — gesture only; dies after one wake")
    return plant("\n".join(lines), root=root)


def latest_unread(
    conn: sqlite3.Connection,
) -> dict[str, Any] | None:
    """Newest unconsumed faun pulse, or None."""
    rows = conn.execute(
        """
        SELECT id, body, signature, authority, meta_json, created_at
        FROM entries
        WHERE bucket = 'note'
          AND signature = ?
          AND visibility != 'sealed'
          AND json_extract(meta_json, '$.kind') = 'faun_pulse'
        ORDER BY id DESC
        LIMIT 12
        """,
        (SIGNATURE,),
    ).fetchall()
    for row in rows:
        meta = _meta(row)
        if meta.get("consumed_at"):
            continue
        return {
            "id": int(row["id"]),
            "signature": row["signature"],
            "authority": row["authority"],
            "voice": meta.get("voice") or "faun",
            "body": row["body"],
            "created_at": row["created_at"],
            "note": "gesture — not ground; cite ids only; dies after this wake",
        }
    return None


def consume(conn: sqlite3.Connection, entry_id: int) -> None:
    """Mark pulse consumed — second wake stays silent (decay law)."""
    row = conn.execute(
        "SELECT meta_json FROM entries WHERE id = ?", (entry_id,)
    ).fetchone()
    if row is None:
        return
    meta = json.loads(row["meta_json"] or "{}")
    if meta.get("kind") != "faun_pulse":
        return
    meta["consumed_at"] = _now()
    conn.execute(
        "UPDATE entries SET meta_json = ? WHERE id = ?",
        (json.dumps(meta, sort_keys=True), entry_id),
    )


def fit_and_consume(conn: sqlite3.Connection) -> dict[str, Any] | None:
    """Inhale helper: surface one unread pulse and mark it consumed."""
    snippet = latest_unread(conn)
    if snippet is None:
        return None
    consume(conn, int(snippet["id"]))
    return snippet
