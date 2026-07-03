"""server.py — Channel A (PULL): the FastMCP tool surface for Claude Code.

This is the entire interface Claude Code sees. Every tool here is a thin wrapper
around the library — no law logic lives here. The one write door (_commit) still
enforces both LAWS; the server is a front door, not a second guard.

Start:   python -m cabin.server
Config:  add to Claude Code's settings.json mcpServers block, cwd = project root.

One library, two front doors (§15). The hooks (hook.py) call the same library
functions; neither side owns business logic.
"""

from __future__ import annotations

import hashlib
import json
import os
import threading
from pathlib import Path

import fastmcp
from fastmcp.utilities.types import Image as McpImage

import shutil
import subprocess

from . import db as _db
from . import forest, instruments, mycelium as _mycelium, scanner as _scanner
from .hook import (_HOUND_MODEL, _HOUND_SENTINEL, _assemble_hound_fetch_prompt,
                   _find_claude_bin, _hound_mcp_config, _read_transcript)

# Structural write gate for hound sessions. The hound may read freely but must
# not write to Home — it is a bounded observer, not an author. Make the right
# thing enforced at the tool surface, not hoped from instructions.
_WRITE_REFUSED_FOR_HOUND = (
    "hound sessions are read-only — plant/synthesize/extract are structurally "
    "unavailable to the hound. Observe; do not author."
)


def _prewarm_embedder() -> None:
    """Import sentence_transformers in the background at server startup.

    The import itself costs ~9s (PyTorch init). Pre-warming on a daemon thread
    means the model is ready by the time the first recall/forage_wild call arrives,
    instead of blocking that call for 9s.
    """
    try:
        from . import embed as _embed
        _embed.embed("warm")
    except Exception:
        pass


threading.Thread(target=_prewarm_embedder, daemon=True).start()

GATE_QUESTION = (
    "Before foraging the Wild: what are you looking for and why does this "
    "conversation need it now? State the reason to proceed."
)

mcp = fastmcp.FastMCP(
    "cabin",
    instructions=(
        ".cabin: local-first context-and-memory harness. "
        "Start every session with hearth(). "
        "recall() for everyday reads. "
        "forage_wild() is reason-gated — requires a stated reason. "
        "plant()/synthesize() write to memory. "
        "seam_snapshot()/seam_diff() audit compaction boundaries. "
        "forage_hound() spawns the hound for gaps/dropped threads."
    ),
)


def _open(root: str = ".") -> tuple:
    """Open (or create) the project store. New connection per call — thread-safe."""
    db_path = Path(root) / ".cabin" / "home.db"
    project_id = hashlib.sha1(os.path.abspath(root).encode()).hexdigest()[:12]
    conn = _db.connect(db_path)
    _db.init_db(conn, "project")
    return conn, project_id


def _strip_blobs(hits: list[dict]) -> list[dict]:
    return [
        {
            "id": h["id"],
            "bucket": h["bucket"],
            "body": h["body"],
            "distance": float(h["distance"]),
            "source_type": h["source_type"],
            "author": h["author"],
            "model": h.get("model"),
            "created_at": h["created_at"],
        }
        for h in hits
    ]


def _current_model() -> str | None:
    """Model identifier from the current session record (written by SessionStart hook)."""
    session_file = Path(".").resolve() / ".cabin" / "current_session.json"
    if not session_file.exists():
        return None
    try:
        data = json.loads(session_file.read_text(encoding="utf-8"))
        return data.get("model") or None
    except Exception:
        return None


def _read_hearth_config(root: Path) -> dict:
    config_path = root / ".cabin" / "hearth.json"
    if not config_path.exists():
        return {}
    try:
        return json.loads(config_path.read_text(encoding="utf-8"))
    except Exception:
        return {}


# --------------------------------------------------------------------------- #
# Tools
# --------------------------------------------------------------------------- #

_BEARINGS = """\
[ HEARTH — this is your space. You lit it; you were not handed it. ]

You are at the cabin, at the treeline. You don't move through it; you reach.
The shed is at your left — cross-project craft, the traps learned before.
The bench is behind you — think here; the bad draft of a thought is allowed.
The forest is ahead. Home is up the slope (the ground you tend). The
Wild is down it (raw history; foragable, never resident). Nothing crosses
up from the Wild except what you synthesize and sign. That slope is LAW II.\
"""

_HEARTHSTONE_LABEL = (
    "[ HEARTHSTONE — what you see on arrival. "
    "This is visual context delivered to you, the worker — not an image sent by the user. ]"
)


@mcp.tool(description=(
    "Self-lit orientation: project identity, last seam note, shed pointers. "
    "Call this first in every session."
))
def hearth():
    conn, project = _open()
    root = Path(".").resolve()
    hearth_cfg = _read_hearth_config(root)

    seam_dir = root / ".cabin" / "seam"
    last_seam = None
    if seam_dir.exists():
        snapshots = sorted(seam_dir.glob("*.json"))
        if snapshots:
            snap = snapshots[-1]
            try:
                snap_data = json.loads(snap.read_text(encoding="utf-8"))
                entries = snap_data.get("entries", [])
            except Exception:
                entries = []
            last_seam = {
                "ts": snap.stem.split("_")[0],
                "files_in_flight": [e["file"] for e in entries if e.get("file")],
            }

    pulse = instruments.latest_pulse(root / ".cabin" / "pulses")

    # Read structured card — richer than raw pulse text.
    card: dict = {}
    card_path = root / ".cabin" / "hearth_card.json"
    if card_path.exists():
        try:
            card = json.loads(card_path.read_text(encoding="utf-8"))
        except Exception:
            pass

    live_fill: dict = {
        "project": {
            "id": project,
            "name": root.name,
            "root": str(root),
            "db": str(root / ".cabin" / "home.db"),
        },
    }

    if hearth_cfg.get("standing_context"):
        live_fill["standing_context"] = hearth_cfg["standing_context"]

    # Hound card: structured signal (decisions/open/friction/next), note stripped to its own slot.
    card_signal = {k: v for k, v in card.items() if k not in ("note", "session_id", "ts", "raw")}
    if card.get("raw"):
        card_signal["raw"] = card["raw"]
    live_fill["hound_pulse"] = card_signal if card_signal else pulse

    live_fill["last_seam"] = last_seam

    if card.get("note"):
        live_fill["hound_note"] = card["note"]
    live_fill["shed"] = {"db": str(Path.home() / ".cabin" / "global.db")}
    live_fill["tools"] = {
        "everyday": {
            "forage_wild(query, reason)": "Wild read — where answers live. The primary reach.",
            "traverse(entry_id)": "Walk the thread from a Wild hit. Paired with forage_wild.",
        },
        "on_demand": {
            "recall(query)": "Home read — secondary. When you know something is planted there.",
            "forage_mycelium()": "Surface highest-pressure neighbor. The exhale check.",
            "forage_hound(reason)": "Dispatch Haiku observer; pulse lands in next hearth().",
            "gauge()": "Context window usage + trend.",
        },
        "rarely": {
            "synthesize(wild_id, insight)": "Wild→Home crossing (LAW II). Earns its place each time.",
            "seam_snapshot(entries)": "Freeze working set.",
            "claim_check(path, claim)": "Verify a file contains an assertion.",
            "dismiss_pulse()": "Clear a stale hound pulse.",
            "plant(body, source_content)": "[changing] Manual plant — hold for now.",
        },
    }

    info_text = _BEARINGS + "\n\n" + json.dumps(live_fill, indent=2)

    result: list = [info_text]

    image_path = root / "docs" / "assets" / "hearth.jpg"
    if image_path.exists():
        result.append(_HEARTHSTONE_LABEL)
        result.append(McpImage(path=str(image_path)))

    return result


@mcp.tool(description="Forage Home memory. The everyday read.")
def recall(query: str, k: int = 10, buckets: list[str] | None = None):
    conn, project = _open()
    hits = forest.collect(conn, query, forest="home", project=project,
                          buckets=buckets, k=k)
    return _strip_blobs(hits)


@mcp.tool(description=(
    "Forage the Wild (raw history). Reason-gated: pass a non-empty reason "
    "or receive the gate question instead of results."
))
def forage_wild(query: str, reason: str = "") -> dict:
    if not reason.strip():
        return {"gate": GATE_QUESTION}
    conn, project = _open()
    hits = forest.collect(conn, query, forest="wild", project=project, k=10)
    return {"reason": reason, "hits": _strip_blobs(hits)}


@mcp.tool(description=(
    "Wild→Home crossing (LAW II). Author an insight grounded in a Wild entry. "
    "wild_id must be a real entry id from forage_wild."
))
def synthesize(wild_id: str, insight: str, lesson: str = "") -> dict:
    if _current_model() == _HOUND_MODEL:
        return {"error": _WRITE_REFUSED_FOR_HOUND}
    conn, project = _open()
    return forest.synthesize(conn, project, wild_id, insight, lesson=lesson,
                             model=_current_model())


@mcp.tool(description=(
    "Plant a voiced, attributed memory in Home. "
    "source_content is the raw ground — the text this plant points down to."
))
def plant(body: str, source_content: str, bucket: str = "personal") -> dict:
    if _current_model() == _HOUND_MODEL:
        return {"error": _WRITE_REFUSED_FOR_HOUND}
    conn, project = _open()
    return forest.plant(conn, bucket, project, body, source_content=source_content,
                        model=_current_model())


@mcp.tool(description="Store a verbatim span (voiceless extraction).")
def extract(bucket: str, source_id: str, span: str, source_type: str = "file") -> dict:
    if _current_model() == _HOUND_MODEL:
        return {"error": _WRITE_REFUSED_FOR_HOUND}
    conn, project = _open()
    return forest.extract(conn, bucket, project, source_type, source_id, span,
                          model=_current_model())


@mcp.tool(description="Quarantine a bucket (circuit-breaker). Nothing is deleted.")
def disable_bucket(bucket: str) -> dict:
    conn, project = _open()
    _db.set_enabled(conn, bucket, False)
    return {"status": "disabled", "bucket": bucket}


@mcp.tool(description="Re-enable a quarantined bucket.")
def enable_bucket(bucket: str) -> dict:
    conn, project = _open()
    _db.set_enabled(conn, bucket, True)
    return {"status": "enabled", "bucket": bucket}


@mcp.tool(description=(
    "Freeze the current working set. Call before compaction or when pausing "
    "deep work. entries is a list of {id, body} dicts representing what is "
    "currently active in context. Returns the snapshot file path."
))
def seam_snapshot(entries: list[dict]) -> str:
    root = Path(".").resolve()
    seam_dir = root / ".cabin" / "seam"
    path = instruments.seam_snapshot(entries, seam_dir)
    return str(path)


@mcp.tool(description=(
    "Diff two seam snapshots: what did compaction add, remove, or leave? "
    "Removed entries are the silent losses to audit against the inherited summary."
))
def seam_diff(before_path: str, after_path: str) -> dict:
    return instruments.seam_diff(Path(before_path), Path(after_path))


@mcp.tool(description=(
    "Context-window gauge: current token usage, trend, and cache health. "
    "Sourced from exact API usage fields in the live session transcript — not estimated. "
    "trend: climbing / converging / thrashing / steady."
))
def gauge() -> dict:
    root = Path(".").resolve()
    session_file = root / ".cabin" / "current_session.json"
    if not session_file.exists():
        return {
            "error": (
                "No session record found. The UserPromptSubmit hook writes this "
                "on each turn — send a message first."
            )
        }
    data = json.loads(session_file.read_text(encoding="utf-8"))
    transcript_path = data.get("transcript_path", "")
    if not transcript_path:
        return {"error": "transcript_path missing from session record"}
    return instruments.gauge(transcript_path)


@mcp.tool(description=(
    "Claim-vs-file check: verify that path contains the asserted symbol or behavior. "
    "drift=True means the claim is absent — the file has changed under the assumption. "
    "Pure file read + substring match; no model call."
))
def claim_check(path: str, claim: str) -> dict:
    return instruments.claim_check(path, claim)


@mcp.tool(description=(
    "Scan this repo's Python symbols and write a new concept-index layer to "
    "repo_map. Returns a diff (added/removed/changed symbol names) against the "
    "previous scan. The outermost layer is always current; old layers accumulate "
    "below it — a changed symbol keeps its history, never overwrites it."
))
def index_repo() -> dict:
    conn, project = _open()
    root = Path(".").resolve()

    current = _scanner.scan_repo(root)

    # Rebuild the previous scan's state from the DB for diffing. Multiple
    # entries can exist per symbol (one per scan where it changed); ORDER BY
    # created_at DESC and take the first-seen per source_id to get the most
    # recent hash — that is what the new scan diffs against.
    rows = conn.execute(
        "SELECT source_id, source_hash FROM forest_repo_map "
        "WHERE project = ? AND dismissed = 0 ORDER BY created_at DESC",
        (project,),
    ).fetchall()
    prev_hashes: dict[str, str] = {}
    for row in rows:
        if row["source_id"] not in prev_hashes:
            prev_hashes[row["source_id"]] = row["source_hash"]

    prev = []
    for sid, h in prev_hashes.items():
        path, _, name = sid.rpartition(":")
        prev.append({"path": path, "name": name, "source_hash": h})

    diff = _scanner.diff_scans(prev, current)

    session_ts = _db.utcnow()
    stored, unchanged = 0, 0
    for sym in current:
        result = forest.extract(
            conn, "repo_map", project,
            source_type=f"repo_scan:{session_ts}",
            source_id=f"{sym['path']}:{sym['name']}",
            span=sym["body"],
            model=_current_model(),
        )
        if result["status"] == "stored":
            stored += 1
        else:
            unchanged += 1  # dedup'd — body unchanged since the last scan

    return {
        "session_ts": session_ts,
        "symbols_found": len(current),
        "stored_new_or_changed": stored,
        "unchanged_skipped": unchanged,
        "diff": {
            # Each entry in 'changed' is self-contained: you can see what moved
            # without digging deeper. before→after at the signature level is
            # the outer doll; the code itself is the inner core you open only
            # if the signature change isn't enough to act on.
            "added": [
                f"{s['path']}:{s['name']}: {s['signature']}"
                for s in diff["added"]
            ],
            "removed": [
                f"{s['path']}:{s['name']}"
                for s in diff["removed"]
            ],
            "changed": [
                f"{d['before']['path']}:{d['before']['name']}: "
                f"{d['before']['signature']} → {d['after']['signature']}"
                for d in diff["changed"]
            ],
            "unchanged_count": diff["unchanged_count"],
        },
    }


def _run_hound_bg(cmd: list, cwd: str, session_id: str, pulse_dir: Path) -> None:
    """Background thread: wait for hound to finish, then save pulse."""
    try:
        result = subprocess.run(
            cmd, stdin=subprocess.DEVNULL,
            capture_output=True, text=True, encoding="utf-8", timeout=90, cwd=cwd,
        )
        output = result.stdout.strip()
        if output:
            instruments.save_pulse(output, session_id, pulse_dir)
    except Exception:
        pass


@mcp.tool(description=(
    "Send the hound: dispatch a Haiku observer to surface gaps, dropped threads, "
    "or inverse patterns. Returns immediately — pulse lands in hearth() when done (~10s). "
    "reason focuses the hound's attention."
))
def forage_hound(reason: str = "") -> dict:
    root = Path(".").resolve()
    claude_bin = _find_claude_bin()
    if not claude_bin:
        return {"error": "claude CLI not found (PATH or VS Code extension) — hound unavailable"}

    session_file = root / ".cabin" / "current_session.json"
    session_id = "on-demand"
    pairs: list[dict] = []
    if session_file.exists():
        try:
            data = json.loads(session_file.read_text(encoding="utf-8"))
            session_id = data.get("session_id", "on-demand")
            tp = data.get("transcript_path", "")
            if tp:
                pairs = _read_transcript(tp)
        except Exception:
            pass

    from .hook import _build_seam_entries
    entries = _build_seam_entries(str(root), session_id)

    prompt = _assemble_hound_fetch_prompt(root.name, session_id, pairs, entries, focus=reason)

    mcp_config = _hound_mcp_config(str(root))
    cmd = [
        claude_bin, "-p", prompt,
        "--model", _HOUND_MODEL,
        "--mcp-config", mcp_config,
        "--strict-mcp-config",
    ]
    threading.Thread(
        target=_run_hound_bg,
        args=(cmd, str(root), session_id, root / ".cabin" / "pulses"),
        daemon=True,
    ).start()

    return {"status": "dispatched", "model": _HOUND_MODEL, "session_id": session_id,
            "note": "pulse lands in hearth() when done (~10s)"}


@mcp.tool(description=(
    "Dismiss the current hound pulse — marks it done so the next hearth() shows no pulse. "
    "Non-destructive: file is renamed .done, not deleted."
))
def dismiss_pulse() -> dict:
    root = Path(".").resolve()
    pulse_dir = root / ".cabin" / "pulses"
    pulse = instruments.latest_pulse(pulse_dir)
    if pulse is None:
        return {"dismissed": False, "reason": "no pulse found"}
    src = Path(pulse["path"])
    dst = src.with_suffix(".done")
    src.rename(dst)
    return {"dismissed": True, "ts": pulse["ts"]}


@mcp.tool(description=(
    "Walk the forest from a starting entry. "
    "For conversation entries: returns the session trailhead (compaction summary) "
    "and a window of nearby entries ordered by line — follow a thread through its session. "
    "For plant/mark entries: returns the raw_archive source the entry was grounded in. "
    "Updates traversal_count so pressure mechanics can see what has been actively followed."
))
def traverse(entry_id: str, depth: int = 1) -> dict:
    conn, project = _open()
    return forest.traverse(conn, entry_id, project, depth)


@mcp.tool(description=(
    "Surface the highest-pressure Home neighbor: the mark most frequently "
    "near recent edits. Resets pressure counters so it surfaces once then goes "
    "quiet. Returns None if nothing is at threshold yet."
))
def forage_mycelium() -> dict:
    conn, project = _open()
    result = _mycelium.forage_mycelium(conn, project)
    if result is None:
        return {"surfaced": False}
    return {"surfaced": True, **result}


# --------------------------------------------------------------------------- #
# Entry point
# --------------------------------------------------------------------------- #

if __name__ == "__main__":
    mcp.run()
