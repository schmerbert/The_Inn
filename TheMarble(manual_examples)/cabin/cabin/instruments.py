"""instruments.py — proprioception for the worker.

Five instruments, all operating outside the embedded forest:

  gauge                — context-window fullness from live transcript usage fields
  claim_check          — verify a file contains an asserted symbol/behavior
  archive_session_raw  — verbatim session transcript → JSONL file (never embedded)
  seam_snapshot        — freeze a working-set before compaction → JSON file
  seam_diff            — diff two seam snapshots (what did the summary drop?)

None of these touch the vector layer. They are the cold, human-readable audit
trail: total fidelity, no filtering, no retrieval path.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path


def _utcnow_slug() -> str:
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    return f"{ts}_{uuid.uuid4().hex[:8]}"


# Tools that only GATHER — reads and searches. A round whose tool calls are all
# in this set is a "search round": digging, not resolving. A write (Edit/Write/
# plant/…) or a plain text answer is resolution and breaks the streak. Bare names
# only; MCP prefixes are stripped before the check, so 'mcp__cabin__recall'
# reads as 'recall'. Tune the membership as new reach-tools appear.
_SEARCH_TOOLS = frozenset({
    "Read", "Grep", "Glob", "recall", "forage_wild", "forage_mycelium",
    "ToolSearch",
})

# How many consecutive search-only rounds (with context still climbing) count as
# thrashing. Three: a couple of looks in and still only digging is the moment the
# bench rule says to stop and ask for the pointer. Tune after real session data.
_THRASH_STREAK = 3


def _tool_names(content) -> list[str]:
    """Bare tool names used in an assistant message's content (MCP prefixes
    stripped: 'mcp__cabin__recall' → 'recall'). Empty if the round called no
    tools — i.e. a plain text answer."""
    names: list[str] = []
    if isinstance(content, list):
        for block in content:
            if isinstance(block, dict) and block.get("type") == "tool_use":
                name = block.get("name", "")
                names.append(name.split("__")[-1] if name else name)
    return names


def _is_search_round(names: list[str]) -> bool:
    """True iff the round called tools and every one only gathers — digging with
    no resolution. A write or an answer (no tools) makes this False."""
    return bool(names) and all(n in _SEARCH_TOOLS for n in names)


def _thrashing(seen: list[dict]) -> bool:
    """Going in circles, read from the tool-call stream: the last _THRASH_STREAK
    rounds are all search-only AND context kept climbing across them. This is the
    honest signal — a variance test on token deltas can't see it (real circling
    is *steady* deltas) and false-fires on ordinary mixed turn sizes."""
    if len(seen) < _THRASH_STREAK:
        return False
    last = seen[-_THRASH_STREAK:]
    if not all(s["search_round"] for s in last):
        return False
    return last[-1]["total_in"] > last[0]["total_in"]


def gauge(transcript_path: str | Path, window: int = 200_000) -> dict:
    """Read exact token usage from the live session JSONL transcript.

    Each assistant message in the transcript carries a 'usage' field from the
    API response — input_tokens, cache_read_input_tokens, cache_creation_input_tokens,
    output_tokens. We deduplicate by run-length (same turn logs multiple lines) and
    return the last turn's counts plus a trend signal over recent turns.

    trend:
      thrashing  — a streak of search-only rounds (Read/Grep/recall/…) with no
                   write or answer between them while context keeps climbing:
                   reaching in circles. Read from the TOOL-CALL STREAM, not token
                   deltas — real circling produces *steady* deltas, so a variance
                   test both missed it and false-fired on ordinary mixed turn
                   sizes (a big read beside a short reply). This is the one meant
                   to trip bench rule 2: stop and ask for the pointer.
      climbing   — last turn added >1,500 tokens (active tool use / large responses)
      converging — last 3 turn deltas all declining (work winding down)
      steady     — none of the above

    Order matters: thrashing is checked first. During real thrashing the context
    is also climbing, but 'thrashing' is the more specific, more actionable read,
    so it wins.
    """
    path = Path(transcript_path)
    if not path.exists():
        return {"error": "transcript not found", "path": str(transcript_path)}

    seen: list[dict] = []
    prev_key: tuple | None = None

    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue
        if obj.get("type") != "assistant":
            continue
        usage = obj.get("message", {}).get("usage")
        if not usage:
            continue
        total_in = (
            usage.get("input_tokens", 0)
            + usage.get("cache_read_input_tokens", 0)
            + usage.get("cache_creation_input_tokens", 0)
        )
        out = usage.get("output_tokens", 0)
        key = (total_in, out)
        if key != prev_key:
            names = _tool_names(obj.get("message", {}).get("content"))
            seen.append({
                "total_in": total_in,
                "output_tokens": out,
                "cache_read": usage.get("cache_read_input_tokens", 0),
                "search_round": _is_search_round(names),
            })
            prev_key = key

    if not seen:
        return {"error": "no assistant turns found", "window": window}

    last = seen[-1]
    total_in = last["total_in"]
    pct = round(total_in / window * 100, 1)
    cache_pct = round(last["cache_read"] / total_in * 100, 1) if total_in else 0.0

    # Thrashing is behavioral (tool-call stream) and checked first — see the
    # docstring. The remaining trends are read from the token deltas.
    trend = "steady"
    if _thrashing(seen):
        trend = "thrashing"
    elif len(seen) >= 2:
        deltas = [seen[i]["total_in"] - seen[i - 1]["total_in"] for i in range(1, len(seen))]
        recent = deltas[-3:]
        last_delta = recent[-1]
        if last_delta > 1500:
            trend = "climbing"
        elif len(recent) >= 3 and all(recent[i] < recent[i - 1] for i in range(1, len(recent))):
            trend = "converging"

    result = {
        "total_in": total_in,
        "output_tokens": last["output_tokens"],
        "pct": pct,
        "trend": trend,
        "turns": len(seen),
        "cache_pct": cache_pct,
        "window": window,
        "free": window - total_in,
    }
    if trend == "thrashing":
        result["hint"] = "consider forage_hound() to surface the gap"
    return result


def claim_check(path: str | Path, claim: str) -> dict:
    """Verify that a file contains the asserted symbol or behavior.

    Reads the file at path and tests whether claim is a substring of the
    content (case-sensitive). Returns the surrounding lines on match.

    drift=True is the flag: the claim is no longer present, investigate.
    No model call; pure file read + match.
    """
    p = Path(path)
    if not p.exists():
        return {
            "path": str(path), "claim": claim,
            "found": False, "drift": True,
            "error": "file not found", "match_context": None,
        }
    try:
        content = p.read_text(encoding="utf-8")
    except Exception as exc:
        return {
            "path": str(path), "claim": claim,
            "found": False, "drift": True,
            "error": str(exc), "match_context": None,
        }

    found = claim in content
    match_context = None
    if found:
        lines = content.splitlines()
        for i, line in enumerate(lines):
            if claim in line:
                start = max(0, i - 1)
                end = min(len(lines), i + 3)
                match_context = "\n".join(
                    f"{start + j + 1}: {lines[start + j]}" for j in range(end - start)
                )
                break

    return {
        "path": str(p.resolve()),
        "claim": claim,
        "found": found,
        "drift": not found,
        "match_context": match_context,
    }


def archive_session_raw(session_id: str, exchanges: list[dict], raw_dir: Path | str) -> Path:
    """Write all exchanges verbatim to <raw_dir>/<session_id>.jsonl.

    Append-only: if the file exists (session already in progress) new exchanges
    are appended. Scaffolding is NOT filtered — this is cold backup, total
    fidelity. Each line: {"seq": int, "text": str, "archived_at": str}.
    Returns the path written to."""
    raw_dir = Path(raw_dir)
    raw_dir.mkdir(parents=True, exist_ok=True)
    out = raw_dir / f"{session_id}.jsonl"
    now = datetime.now(timezone.utc).isoformat()
    with open(out, "a", encoding="utf-8") as f:
        for ex in exchanges:
            line = {"seq": ex.get("seq"), "text": ex.get("text", ""), "archived_at": now}
            f.write(json.dumps(line, ensure_ascii=False) + "\n")
    return out


def seam_snapshot(working_set: list[dict], seam_dir: Path | str) -> Path:
    """Freeze the working set to <seam_dir>/<ts>.json.

    Each call creates a new timestamped file — never overwrites an existing one.
    A fresh instance uses seam_diff to audit what the compaction summary omitted.
    Returns the path written."""
    seam_dir = Path(seam_dir)
    seam_dir.mkdir(parents=True, exist_ok=True)
    ts = _utcnow_slug()
    out = seam_dir / f"{ts}.json"
    out.write_text(json.dumps({"ts": ts, "entries": working_set}, indent=2, ensure_ascii=False),
                   encoding="utf-8")
    return out


def save_pulse(text: str, session_id: str, pulse_dir: Path | str) -> Path:
    """Write a hound pulse to <pulse_dir>/<ts>_<session_id[:8]>.md.

    Each call creates a new timestamped file. The hearth reads the latest one
    at session-start so the hound's observations land before the first turn.
    Returns the path written."""
    pulse_dir = Path(pulse_dir)
    pulse_dir.mkdir(parents=True, exist_ok=True)
    ts = _utcnow_slug()
    out = pulse_dir / f"{ts}_{session_id[:8]}.md"
    out.write_text(text, encoding="utf-8")
    return out


def latest_pulse(pulse_dir: Path | str) -> dict | None:
    """Return the most-recent pulse as {text, path, ts}, or None if none exist."""
    pulse_dir = Path(pulse_dir)
    if not pulse_dir.exists():
        return None
    files = sorted(pulse_dir.glob("*.md"))
    if not files:
        return None
    latest = files[-1]
    return {
        "text": latest.read_text(encoding="utf-8"),
        "path": str(latest),
        "ts": latest.stem,
    }


def seam_diff(before_path: Path | str, after_path: Path | str) -> dict:
    """Compare two seam snapshots by entry id. Returns:
      added     — in after, not in before  (context gained)
      removed   — in before, not in after  (dropped at compaction — audit these)
      unchanged — in both

    A removed entry is the loss a fresh instance should interrogate: was it
    captured in the compaction summary, or silently gone?"""
    before = {e["id"]: e for e in json.loads(Path(before_path).read_text(encoding="utf-8"))["entries"]}
    after  = {e["id"]: e for e in json.loads(Path(after_path).read_text(encoding="utf-8"))["entries"]}

    added     = [i for i in after  if i not in before]
    removed   = [i for i in before if i not in after]
    unchanged = [i for i in before if i in after]

    return {
        "added":     {"count": len(added),     "ids": added},
        "removed":   {"count": len(removed),   "ids": removed},
        "unchanged": {"count": len(unchanged), "ids": unchanged},
    }
