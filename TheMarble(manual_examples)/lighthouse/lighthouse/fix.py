"""The Fix gate — the only crossing into the LOG.

A fix is a claim with evidence taken at a moment. Dead reckoning is legal
and lives on the chart; the poison is only ever the missing label.
Every attempt, passed or refused, lands in fix_audit.
"""

from __future__ import annotations

import sqlite3
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone

EVIDENCE_TYPES = ("command", "file-read", "user-said")

# Evidence that is itself inherited prose. A handoff is not a sighting;
# neither is a summary, a memory, or the cottage.
HEARSAY_MARKERS = (
    "handoff",
    "previous session",
    "prior session",
    "compaction",
    "summary of",
    "as summarized",
    "journal",
    "cottage",
    "i remember",
    "from memory",
)


class FixRefused(Exception):
    def __init__(self, reason: str):
        self.reason = reason
        super().__init__(reason)


@dataclass
class FixRequest:
    claim: str
    evidence_type: str
    evidence: str
    verified_against: str
    author: str


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _audit(conn: sqlite3.Connection, req: FixRequest, outcome: str, reason: str) -> None:
    conn.execute(
        "INSERT INTO fix_audit (attempted_at, claim, evidence_type, author, outcome, reason)"
        " VALUES (?, ?, ?, ?, ?, ?)",
        (_now(), (req.claim or "").strip(), req.evidence_type, req.author, outcome, reason),
    )
    conn.commit()


def _refuse(conn: sqlite3.Connection, req: FixRequest, reason: str) -> None:
    _audit(conn, req, "refused", reason)
    raise FixRefused(reason)


def take_fix(conn: sqlite3.Connection, req: FixRequest) -> str:
    """Attempt the crossing. Returns fix id or raises FixRefused."""
    claim = (req.claim or "").strip()
    if not claim:
        _refuse(conn, req, "empty claim — nothing to log")

    if req.evidence_type not in EVIDENCE_TYPES:
        _refuse(
            conn, req,
            f"dead reckoning is not a fix — evidence_type must be one of {EVIDENCE_TYPES}",
        )

    evidence = (req.evidence or "").strip()
    if not evidence:
        _refuse(conn, req, "dead reckoning is not a fix — a sighting requires evidence")

    lowered = evidence.lower()
    for marker in HEARSAY_MARKERS:
        if marker in lowered:
            _refuse(
                conn, req,
                f"a handoff is not a sighting — evidence cites inherited prose ('{marker}');"
                " re-verify against the world, or plot it on the chart as DR",
            )

    if not (req.verified_against or "").strip():
        _refuse(
            conn, req,
            "a fix must say what it was verified against (commit, path+date, or session)",
        )

    if not (req.author or "").strip():
        _refuse(conn, req, "unsigned — every fix carries its keeper's signature")

    fix_id = f"fix-{uuid.uuid4().hex[:10]}"
    conn.execute(
        "INSERT INTO fix (id, claim, evidence_type, evidence, verified_against, taken_at, author)"
        " VALUES (?, ?, ?, ?, ?, ?, ?)",
        (fix_id, claim, req.evidence_type, evidence,
         req.verified_against.strip(), _now(), req.author.strip()),
    )
    _audit(conn, req, "fixed", f"fixed via {req.evidence_type}")
    return fix_id
