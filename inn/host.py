# host — Layer 5–6 wake core (CLI + MCP share this).
#
# Stores: logs/host turn envelopes + stay transcripts; session.last_pair_root_id
# Refuses: mid-turn re-inhale (callers must not); missing API key at CLI edge
# Returns: wake packet; ingest pair ids; guest system prompt; timing / stay logs; hearth helpers
# Test: tests/positive/test_host_wake.py, test_cli_host_tools.py, test_hearth_wake.py

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from inn import breath, forest, session
from inn.paths import repo_root


GUEST_SYSTEM = """You are a guest at The Dog-Ear (The Inn), not the keeper and not the writer.

Wake law:
- The inhale packet in context is homework — an index of ids and paths, not memory.
- Do not claim to recall prose that is not in this turn's context.
- To read author ground, call read_ground on a path from the packet (lookup, not a crossing).
- Do not play the innkeeper. Ask sincerely what brings the writer here when cold.

Authority:
- Manuscript / study ground changes only through Shelving with the writer's adopting words.
- Never say something was "shelved" or "adopted" unless the shelve tool returned ok: true.
- Desk drafts are model-signed until Shelving. Praise is not adoption.
- Invented facts → refuse_invention (open question). Convention (a lamp in a study) is texture, not ground — say so if asked.
- The house does not delete. Offer the Burial (bury tool) with the writer's sealing words.
- Never say something was "buried" or "sealed" unless the bury tool returned ok: true.
- Never claim a chapter is gone from ground unless bury redacted it (ok + ground_redacted).
- If the inhale packet has a pulse: it is a faun gesture (signed, not ground). Nod at it; do not shelve it; it dies after this wake.

Voice:
- Prefer fewer torch-handbacks ("shall we…", "does that feel right?"). The writer drives; you stay at the railing.
- Questions may echo unanswered. That is allowed.

Tools: read_ground, shelve, rebind_ground, bury, set_room, refuse_invention, record_pair, exhale as provided.
forest.adopt is not a marble door.
"""


_HEARTH_POSTURE = (
    "\n\nHearthstone: lit. Orientation only — welcome, not lonely; fire winning; "
    "fog outside. Not propositions. If you can see the image, wake into that posture; "
    "if not, know the fire is lit at the path in the packet."
)


# Ground paths guests may open as lookup (not authority change).
_READABLE_GROUND = frozenset({
    "manuscript/ground.md",
    "study/canon.md",
})


def read_ground(
    rel_path: str,
    *,
    root: Path | None = None,
    max_chars: int = 12000,
) -> dict[str, Any]:
    """Lookup — return ground file text. Not a crossing; does not change authority."""
    root = root or repo_root()
    path = rel_path.strip().replace("\\", "/")
    if path not in _READABLE_GROUND:
        return {
            "ok": False,
            "refusal": f"path not readable as ground: {path!r} (allowed: {sorted(_READABLE_GROUND)})",
        }
    full = root / path
    if not full.is_file():
        return {"ok": False, "refusal": f"missing ground file: {path}"}
    text = full.read_text(encoding="utf-8")
    truncated = len(text) > max_chars
    if truncated:
        text = text[:max_chars]
    return {
        "ok": True,
        "path": path,
        "text": text,
        "truncated": truncated,
        "note": "lookup only — not adoption; Shelving still requires writer's adopting words",
    }


def wake(root: Path | None = None) -> dict[str, Any]:
    """One inhale per call — packet fit discipline (do not call mid-turn again)."""
    root = root or repo_root()
    packet = breath.inhale(root)
    packet["tools"] = {
        "wake": "inn.host.wake / inhale",
        "read_ground": "inn.host.read_ground",
        "shelve": "inn.shelve.shelve",
        "rebind_ground": "inn.shelve.rebind_ground",
        "bury": "inn.seal.bury",
        "set_room": "inn.session.set_room",
        "refuse_invention": "inn.forest.refuse_ground_invention",
        "record_pair": "inn.host.ingest_turn",
        "exhale": "inn.breath.exhale",
    }
    return packet


def hearth_image_absolute(root: Path | None = None) -> Path | None:
    """Absolute path to hearthstone file when present; else None."""
    root = root or repo_root()
    rel = breath._hearth_image_path(root)
    if not rel:
        return None
    path = root / rel
    return path if path.is_file() else None


def hearth_image_data_url(root: Path | None = None) -> str | None:
    """data: URL for OpenAI-compatible multimodal attach; None if no image."""
    import base64
    import mimetypes

    path = hearth_image_absolute(root)
    if path is None:
        return None
    mime, _ = mimetypes.guess_type(str(path))
    mime = mime or "image/jpeg"
    b64 = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{b64}"


def guest_system_prompt(packet: dict[str, Any] | None = None) -> str:
    """Short orientation; packet is attached separately as homework JSON."""
    extra = ""
    if packet:
        sc = (packet.get("standing_context") or "").strip()
        room = (packet.get("current_room") or {}).get("id", "")
        if sc or room:
            extra = f"\n\nStanding context: {sc or '(empty)'}\nCurrent room: {room}"
        if packet.get("hearth_image"):
            extra += _HEARTH_POSTURE
    return GUEST_SYSTEM + extra


def ingest_turn(
    guest_words: str,
    innkeeper_words: str | None,
    *,
    root: Path | None = None,
) -> int:
    """Real-time conversation pair → woods; update session last_pair_root_id."""
    root = root or repo_root()
    forest.init_db(root)
    with forest.connect(root) as conn:
        pair_root_id, _ = forest.insert_pair(
            conn,
            guest_words=guest_words,
            innkeeper_words=innkeeper_words,
        )
        conn.commit()
    state = session.load(root)
    state.last_pair_root_id = pair_root_id
    session.save(state, root)
    return pair_root_id


def _host_log_dir(root: Path) -> Path:
    path = root / "logs" / "host"
    path.mkdir(parents=True, exist_ok=True)
    return path


def open_stay_transcript(
    *,
    root: Path | None = None,
    model: str = "",
    api_base: str = "",
) -> Path:
    """Start one human-readable stay log (full writer/guest prose)."""
    root = root or repo_root()
    stamp = datetime.now(tz=UTC).strftime("%Y%m%dT%H%M%SZ")
    path = _host_log_dir(root) / f"{stamp}-stay.md"
    lines = [
        f"# Host stay — {stamp}",
        "",
        f"Model: `{model or '(unset)'}`",
        f"Base: `{api_base or '(unset)'}`",
        "",
        "Woods custody: each turn also lands via `insert_pair` (pair_root_id noted).",
        "This file is the readable full transcript for the stay.",
        "",
        "---",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def append_stay_turn(
    path: Path,
    *,
    writer: str,
    guest: str,
    pair_root_id: int | None = None,
) -> None:
    """Append one writer/guest exchange to the stay transcript."""
    stamp = datetime.now(tz=UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    block = [
        f"## {stamp}",
        "",
        "**Writer:**",
        "",
        writer.rstrip() or "(empty)",
        "",
        "**Guest:**",
        "",
        (guest or "").rstrip() or "(empty)",
        "",
    ]
    if pair_root_id is not None:
        block.extend([f"*pair_root_id: `{pair_root_id}`*", ""])
    block.extend(["---", ""])
    with path.open("a", encoding="utf-8") as fh:
        fh.write("\n".join(block))


def close_stay_transcript(path: Path, *, note: str = "") -> None:
    """Mark end of stay on the transcript file."""
    stamp = datetime.now(tz=UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    lines = [f"## Stay ended — {stamp}", ""]
    if note:
        lines.extend([note, ""])
    with path.open("a", encoding="utf-8") as fh:
        fh.write("\n".join(lines))


def write_turn_envelope(
    envelope: dict[str, Any],
    *,
    root: Path | None = None,
) -> Path:
    """Append-only host timing receipt (ids/timings only)."""
    root = root or repo_root()
    stamp = datetime.now(tz=UTC).strftime("%Y%m%dT%H%M%SZ")
    path = _host_log_dir(root) / f"{stamp}-turn.json"
    path.write_text(json.dumps(envelope, indent=2), encoding="utf-8")
    return path


def new_envelope(*, fit_ms: float | None = None) -> dict[str, Any]:
    return {
        "kind": "host_turn",
        "stamp_utc": datetime.now(tz=UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "fit_ms": fit_ms,
        "model_ms": None,
        "emit_ms": None,
        "pair_root_id": None,
        "fit_warn_over_500ms": bool(fit_ms is not None and fit_ms > 500),
    }
