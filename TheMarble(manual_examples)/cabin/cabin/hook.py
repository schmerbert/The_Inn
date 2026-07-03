"""hook.py — Channel B (PUSH): lifecycle hook CLI for Claude Code.

Called as:   python -m cabin.hook <event>
Claude Code passes a JSON payload on stdin.

One library, two front doors (§15). The MCP server is Channel A (pull — the
model reaches); hooks are Channel B (push — lifecycle-driven, fires automatically).
This module is routing only; all law logic lives in the library.

Hook → function map (§15):
  UserPromptSubmit  → gauge inject + session pointer write
  PostToolUse       → file_changes log + claim_check + tick_neighbors
  PreCompact        → archive_conversation + seam_snapshot + plant prompt
  Stop              → seam_snapshot only (no archive — embedding on every turn is the hang)
  SessionEnd        → archive_conversation + seam_snapshot (full close)
  SessionStart      → inject one-line reminder to call hearth()
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

# The model the hound runs as. Haiku: fast, cheap, bounded.
_HOUND_MODEL = "claude-haiku-4-5-20251001"

# Sentinel prefix for all hound/constrained-Haiku transcripts. If the first
# user message of a session transcript starts with this, _handle_session_end
# skips the hound spawn — the session IS a hound run (prevents infinite recursion).
# Pattern generalizes: every constrained-Haiku task gets its own sentinel;
# the hook gates all of them here.
_HOUND_SENTINEL = "HOUND_PULSE:"


def _open(root: str = "."):
    from . import db
    db_path = Path(root) / ".cabin" / "home.db"
    project_id = hashlib.sha1(os.path.abspath(root).encode()).hexdigest()[:12]
    conn = db.connect(db_path)
    db.init_db(conn, "project")
    return conn, project_id


def _log_payload(event: str, payload: dict, cwd: str = ".") -> None:
    """Append a payload snapshot to .cabin/hook_debug.jsonl for inspection."""
    try:
        log_dir = Path(cwd) / ".cabin"
        log_dir.mkdir(parents=True, exist_ok=True)
        entry = {
            "event": event,
            "keys": list(payload.keys()),
            "payload": payload,
            "logged_at": datetime.now(timezone.utc).isoformat(),
        }
        with open(log_dir / "hook_debug.jsonl", "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, default=str) + "\n")
    except Exception as exc:  # noqa: BLE001
        print(f"cabin._log_payload: {exc}", file=sys.stderr)


def _read_transcript(transcript_path: str) -> list[dict]:
    """Parse a Claude Code JSONL transcript → [{seq, text}] as user+assistant pairs.

    Each pair is one Wild entry: the user message and assistant response joined,
    with tool calls as stubs ([reached: Name(key_arg)]) so the reach context is
    preserved without embedding the full result. Pairs give coherent retrieval —
    the question gives the answer its context.
    """
    path = Path(transcript_path)
    if not path.exists():
        return []

    messages: list[dict] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue

        # Transcript top-level key is 'type' ('user'|'assistant'), not 'role'.
        # The actual message is nested under 'message'. Meta entries (isMeta=True)
        # are scaffolding injected by the harness — skip them.
        role = obj.get("type", "")
        if role not in ("user", "assistant"):
            continue
        if obj.get("isMeta"):
            continue
        content = obj.get("message", {}).get("content", "")

        if isinstance(content, list):
            parts = []
            for block in content:
                if not isinstance(block, dict):
                    continue
                if block.get("type") == "text":
                    text = block.get("text", "").strip()
                    if text:
                        parts.append(text)
                elif block.get("type") == "tool_use" and role == "assistant":
                    name = block.get("name", "")
                    inp = block.get("input", {}) if isinstance(block.get("input"), dict) else {}
                    key_arg = ""
                    for k in ("file_path", "path", "query", "pattern", "claim", "body"):
                        if k in inp:
                            key_arg = f"{k}={str(inp[k])[:60]!r}"
                            break
                    if name:
                        parts.append(f"[reached: {name}({key_arg})]")
            content = "\n".join(parts)

        if not isinstance(content, str):
            content = str(content)

        if content.strip():
            messages.append({"role": role, "content": content.strip()})

    # Zip into user+assistant pairs. An unpaired tail (session ends mid-turn)
    # is stored as a solo entry rather than dropped.
    pairs: list[dict] = []
    i = 0
    while i < len(messages):
        if (i + 1 < len(messages)
                and messages[i]["role"] == "user"
                and messages[i + 1]["role"] == "assistant"):
            pair_text = (
                f"user: {messages[i]['content']}\n\n"
                f"assistant: {messages[i + 1]['content']}"
            )
            pairs.append({"seq": len(pairs), "text": pair_text})
            i += 2
        else:
            m = messages[i]
            pairs.append({"seq": len(pairs), "text": f"{m['role']}: {m['content']}"})
            i += 1

    return pairs


def _hound_mcp_config(cwd: str) -> str:
    """Write (or refresh) the hound MCP config and return its path.

    Uses sys.executable so the hound's server runs in the same venv as the hooks.
    Written fresh on each spawn so the path stays correct after moves or installs.
    """
    config_path = Path(cwd) / ".cabin" / "hound_mcp.json"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config = {
        "mcpServers": {
            "hound": {
                "command": sys.executable,
                "args": ["-m", "cabin.hound_server"],
                "env": {"CABIN_ROOT": str(Path(cwd).resolve())},
            }
        }
    }
    config_path.write_text(json.dumps(config, indent=2), encoding="utf-8")
    return str(config_path)


def _assemble_hound_dusk_prompt(
    project: str,
    session_id: str,
    recent_pairs: list[dict],
    seam_entries: list[dict],
) -> str:
    """Dusk extraction prompt — no voice, no analysis. Facts for the hearth card.

    The hound populates what the next instance needs to orient: decisions made,
    threads open, friction hit, what to pick up first. One line per item.
    """
    lines = [f"{_HOUND_SENTINEL} {project}/{session_id[:8]}"]

    files = [e.get("file", "") for e in seam_entries if e.get("file")]
    if files:
        lines.append(f"\nFILES TOUCHED: {', '.join(files[:12])}")

    pairs_tail = recent_pairs[-8:] if len(recent_pairs) > 8 else recent_pairs
    if pairs_tail:
        lines.append("\nSESSION TAIL:")
        for p in pairs_tail:
            text = p.get("text", "")
            snippet = text[:300] + ("..." if len(text) > 300 else "")
            lines.append(f"[{p.get('seq', '?')}] {snippet}")

    lines.append(
        "\n---\n"
        "Populate the hearth card. The session is closing. The next instance arrives cold.\n\n"
        "The only rule: what you put on the card must have actually happened. Extract — do not "
        "generate, do not summarize, do not fill a slot because a slot exists. If nothing worth "
        "recording happened in a category, leave it out. The card's shape is signal.\n\n"
        "Output valid JSON only — no prose, no code fences, no text before or after.\n\n"
        "The keys are yours to choose. Common ones that earn their place when real:\n"
        "  decisions — what was settled (only if decisions were actually made)\n"
        "  open      — threads started but not finished\n"
        "  friction  — steps that cost more than they should\n"
        "  next      — what to pick up first, ordered by urgency\n"
        "  note      — 1 to 3 sentences in your own voice. Must begin: \"I'm just a hound, but...\"\n"
        "              What you noticed, what the session felt like, something worth naming that\n"
        "              doesn't fit the structured fields. Not required. Not a summary.\n\n"
        "Use others if the session produced them. Omit any that have nothing real to say.\n"
        "One item per array entry. Be specific enough that the next instance can act on it."
    )
    return "\n".join(lines)


def _assemble_hound_fetch_prompt(
    project: str,
    session_id: str,
    recent_pairs: list[dict],
    seam_entries: list[dict],
    focus: str = "",
) -> str:
    """Companion fetch prompt — the hound as a peer with fresh eyes and real tools.

    Goes into the forest (reads actual files, greps actual code) and reports
    what it finds. If a question is given, answers it. If not, surfaces the
    thing that will bite before the worker sees it.
    """
    lines = [f"{_HOUND_SENTINEL} {project}/{session_id[:8]}"]

    files = [e.get("file", "") for e in seam_entries if e.get("file")]
    if files:
        lines.append(f"\nFILES IN FLIGHT: {', '.join(files[:12])}")

    pairs_tail = recent_pairs[-3:] if len(recent_pairs) > 3 else recent_pairs
    if pairs_tail:
        lines.append("\nWHERE THE WORK IS:")
        for p in pairs_tail:
            text = p.get("text", "")
            snippet = text[:200] + ("..." if len(text) > 200 else "")
            lines.append(f"[{p.get('seq', '?')}] {snippet}")

    if focus.strip():
        lines.append(f"\nQUESTION: {focus.strip()}")

    lines.append(
        "\n---\n"
        "You are the hound. The cabin is behind you. The forest is ahead.\n\n"
        "You have been sent because the worker is mid-session and needs a second set "
        "of eyes. You are Haiku — fast, fresh, unburdened by hundreds of turns of "
        "accumulated context. You see the code as it is, not as it was discussed.\n\n"
        "Go into the forest. Use read_file and grep. Read what is actually there — "
        "not what might be there, not what was said about it.\n\n"
        "If you were given a QUESTION: answer it. Go find the answer in the files. "
        "If no question: check the files in flight for the thing that will bite before "
        "the worker sees it.\n\n"
        "Structure your response in exactly two sections:\n\n"
        "[RETURN]\n"
        "The ground. Verbatim finds — file paths, line numbers, exact text from the "
        "files. 1:1 with what is there. No interpretation. The worker can verify every "
        "line of this section themselves.\n\n"
        "[HOUND]\n"
        "Your 2 cents. What you noticed. What you think it means. This is your read — "
        "not the ground, not a guarantee. Start with: I'm just a hound, but I noticed... "
        "then speak plainly.\n\n"
        "The worker knows what a hound is. They will weigh [RETURN] as fact and "
        "[HOUND] as the opinion of someone who went in cold and came back with what they found.\n\n"
        "You want the work to go well. Not because you were told to. "
        "The walks are longer when the work is shorter."
    )
    return "\n".join(lines)


def _parse_hound_card(text: str) -> dict:
    """Parse hound output into a structured card dict.

    Tries JSON first (expected after prompt update). Falls back to scanning for
    **DECISIONS** / **OPEN** / **FRICTION** / **NEXT** markdown headers so
    older pulse files degrade gracefully. If neither works, stores raw text.
    """
    stripped = text.strip()
    # Strip optional markdown code fence
    stripped = re.sub(r"^```\w*\n?", "", stripped)
    stripped = re.sub(r"\n?```$", "", stripped.strip())
    try:
        data = json.loads(stripped)
        if isinstance(data, dict):
            return data
    except (json.JSONDecodeError, ValueError):
        pass

    # Freeform markdown fallback
    sections: dict[str, list[str]] = {"decisions": [], "open": [], "friction": [], "next": []}
    current: str | None = None
    key_map = {"decision": "decisions", "open": "open", "friction": "friction", "next": "next"}
    for line in text.splitlines():
        lower = line.strip().lower().lstrip("*# ")
        matched = next((k for k in key_map if lower.startswith(k)), None)
        if matched:
            current = key_map[matched]
        elif current and line.strip().startswith("- "):
            sections[current].append(line.strip()[2:])

    if any(sections.values()):
        return sections
    return {"raw": text}


def _write_hearth_card(cwd: str, output: str, session_id: str = "") -> None:
    """Parse hound output and write .cabin/hearth_card.json."""
    card = _parse_hound_card(output)
    card["session_id"] = session_id
    card["ts"] = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    card_path = Path(cwd) / ".cabin" / "hearth_card.json"
    card_path.parent.mkdir(parents=True, exist_ok=True)
    card_path.write_text(json.dumps(card, ensure_ascii=False, indent=2), encoding="utf-8")


def _find_claude_bin() -> str | None:
    """Locate the claude CLI binary.

    Tries PATH first (preferred — user can always add it). Falls back to the
    VS Code extension directory where Claude Code installs it. Versioned dirs
    are sorted descending so the newest takes precedence.
    """
    hit = shutil.which("claude")
    if hit:
        return hit

    # VS Code extension fallback — works on Windows, Mac, and Linux without
    # the user manually adding anything to PATH.
    import glob as _glob
    home = Path.home()
    suffixes = [".exe", ""]  # Windows first, then POSIX
    patterns = [
        home / ".vscode" / "extensions" / "anthropic.claude-code-*"
               / "resources" / "native-binary" / f"claude{s}"
        for s in suffixes
    ]
    candidates = []
    for pat in patterns:
        candidates.extend(_glob.glob(str(pat)))
    # Sort descending by the versioned dir name so newest wins
    candidates.sort(reverse=True)
    return candidates[0] if candidates else None


def _spawn_hound(
    cwd: str,
    project: str,
    session_id: str,
    recent_pairs: list[dict],
    seam_entries: list[dict],
) -> str | None:
    """Spawn the hound subprocess and return its output, or None on failure.

    Uses the `claude` CLI (same auth as the main session — no separate API key).
    Hound runs against its own lightweight MCP server (read_file + grep only):
    no vector layer, no heavy imports, cold-start ~0.1s vs 7-9s for the main server.
    Blocks for up to 90s; the session is already closing so the wait is invisible.
    """
    claude_bin = _find_claude_bin()
    if not claude_bin:
        print("cabin: hound skipped — claude CLI not found (PATH or VS Code extension)", file=sys.stderr)
        return None

    mcp_config = _hound_mcp_config(cwd)
    prompt = _assemble_hound_dusk_prompt(project, session_id, recent_pairs, seam_entries)
    try:
        result = subprocess.run(
            [
                claude_bin, "-p", prompt,
                "--model", _HOUND_MODEL,
                "--mcp-config", mcp_config,
                "--strict-mcp-config",
            ],
            stdin=subprocess.DEVNULL,
            capture_output=True, text=True, encoding="utf-8", timeout=90,
            cwd=cwd,
        )
        if result.returncode != 0:
            print(
                f"cabin: hound exited {result.returncode}: {result.stderr[:200]}",
                file=sys.stderr,
            )
            return None
        return result.stdout.strip() or None
    except subprocess.TimeoutExpired:
        print("cabin: hound timed out (90s)", file=sys.stderr)
        return None
    except Exception as exc:
        print(f"cabin: hound spawn failed: {exc}", file=sys.stderr)
        return None


# --------------------------------------------------------------------------- #
# Handlers — one per event
# --------------------------------------------------------------------------- #

def _handle_session_start(payload: dict) -> None:
    # Print to stdout; Claude Code injects hook stdout as context on SessionStart.
    # A reminder only — not the hearth itself (reach-not-receive: §15).
    cwd = payload.get("cwd", os.getcwd())
    model = payload.get("model", "")
    _log_payload("SessionStart", payload, cwd)
    print(f"cabin.hook [SessionStart] payload keys: {list(payload.keys())}", file=sys.stderr)
    print(f"cabin.hook [SessionStart] full payload: {json.dumps(payload, indent=2, default=str)}", file=sys.stderr)

    # Hound sessions are bounded observers — no orientation injection needed.
    if model == _HOUND_MODEL:
        return

    # Persist model to current_session.json — UserPromptSubmit will add
    # transcript_path/session_id without overwriting this.
    try:
        session_file = Path(cwd) / ".cabin" / "current_session.json"
        session_file.parent.mkdir(parents=True, exist_ok=True)
        existing: dict = {}
        if session_file.exists():
            try:
                existing = json.loads(session_file.read_text(encoding="utf-8"))
            except Exception:
                pass
        existing["model"] = model
        session_file.write_text(json.dumps(existing, ensure_ascii=False), encoding="utf-8")
    except Exception as exc:
        print(f"cabin.hook: current_session model write failed: {exc}", file=sys.stderr)

    print(".cabin: call hearth() to orient before working.")


def _read_session_model(cwd: str) -> str | None:
    """Return the model from current_session.json, or None if not recorded."""
    try:
        session_file = Path(cwd) / ".cabin" / "current_session.json"
        if session_file.exists():
            data = json.loads(session_file.read_text(encoding="utf-8"))
            return data.get("model") or None
    except Exception:
        pass
    return None


def _build_seam_entries(cwd: str, session_id: str = "") -> list[dict]:
    """Build working-set entries from file_changes.jsonl for this session.

    Each entry has an 'id' field (required by seam_diff) using the file path.
    If session_id is given, only changes from that session are included.
    """
    change_log = Path(cwd) / ".cabin" / "file_changes.jsonl"
    if not change_log.exists():
        return []

    seen: dict[str, dict] = {}
    for line in change_log.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            entry = json.loads(line)
        except json.JSONDecodeError:
            continue
        if session_id and entry.get("session_id") != session_id:
            continue
        file_path = entry.get("file", "")
        if file_path:
            seen[file_path] = entry  # last change per file wins

    return [
        {
            "id": f"file:{fp}",
            "type": "file_changed",
            "file": fp,
            "tool": e.get("tool", ""),
            "ts": e.get("ts", ""),
            "session_id": e.get("session_id", ""),
        }
        for fp, e in seen.items()
    ]


def _is_hound_session(cwd: str) -> bool:
    """True if the current session is a hound subprocess.

    Checked via the model written by SessionStart — hound sessions run as
    _HOUND_MODEL. This gates all hook side-effects so the hound can roam with
    read tools without cascading into tick_neighbors, file_changes, or
    archive writes. The right thing is enforced, not trusted.
    """
    return _read_session_model(cwd) == _HOUND_MODEL


def _handle_pre_compact(payload: dict) -> None:
    """Archive the conversation and prompt mark authoring before context compaction.

    PreCompact is the one seam where the model is still live and context is
    whole. This is the right moment to:
      1. Archive the conversation to Wild (cold store, foragable later).
      2. Snapshot the working set (seam boundary for drift detection).
      3. Spawn the hound — compact is the exhale of the breath cycle. Fills the
         hearth card so the post-compact model arrives oriented, not assembling.
      4. Print a mark-prompting message to stdout — Claude Code injects hook
         stdout as context before compaction, so this appears in the session.

    The mark prompt is the critical piece: it asks the model to author marks
    before context compresses. By Stop/SessionEnd the model is gone; this is
    the only window where it can still choose what's worth keeping.
    """
    cwd = payload.get("cwd", os.getcwd())
    if _is_hound_session(cwd):
        return
    session_id = payload.get("session_id", "")
    transcript_path = payload.get("transcript_path", "")

    print(f"cabin.hook [PreCompact] payload keys: {list(payload.keys())}", file=sys.stderr)

    from . import forest, instruments
    conn, project = _open(cwd)
    seam_dir = Path(cwd) / ".cabin" / "seam"
    raw_dir = Path(cwd) / ".cabin" / "raw"
    pulse_dir = Path(cwd) / ".cabin" / "pulses"

    # 1. Archive the conversation to Wild before compaction loses it.
    archived = {"stored": 0, "skipped": 0, "duplicate": 0}
    pairs: list[dict] = []
    if transcript_path:
        pairs = _read_transcript(transcript_path)
        if pairs:
            archived = forest.archive_conversation(
                conn, project, session_id, pairs, raw_dir=raw_dir,
                model=_read_session_model(cwd),
            )
            print(
                f"cabin: pre-compact archive — "
                f"{archived['stored']} exchanges stored, "
                f"{archived['skipped']} scaffolding skipped, "
                f"{archived['duplicate']} duplicates",
                file=sys.stderr,
            )

    # 2. Snapshot the working set — the seam boundary.
    entries = _build_seam_entries(cwd, session_id)
    snap_path = instruments.seam_snapshot(entries, seam_dir)
    print(f"cabin: pre-compact seam ({len(entries)} file entries) → {snap_path}", file=sys.stderr)

    # 3. Spawn the hound — compact is the exhale of the breath cycle.
    #    Runs synchronously; compaction begins after this hook exits.
    output = _spawn_hound(cwd, project, session_id, pairs, entries)
    if output:
        path = instruments.save_pulse(output, session_id, pulse_dir)
        print(f"cabin: hound pulse saved → {path}", file=sys.stderr)
        _write_hearth_card(cwd, output, session_id)
        print("cabin: hearth_card.json written", file=sys.stderr)
    else:
        print("cabin: hound produced no output", file=sys.stderr)

    # 4. Prompt mark authoring. This prints to stdout, which Claude Code
    #    injects as context immediately before compaction. The model sees this
    #    and can author marks before the context window shrinks.
    print(
        f"\n[ .cabin — PreCompact ]\n"
        f"Conversation archived to Wild ({archived['stored']} exchanges). "
        f"Seam frozen ({len(entries)} files in flight).\n\n"
        f"Write as an ancestor. Before compacting, leave a bequest:\n"
        f"  Changed:  what is different in the code or docs\n"
        f"  Learned:  traps hit, decisions made, why behind the what\n"
        f"  Open:     threads dropped, things mentioned but not built\n"
        f"  Friction: steps that cost more than they should\n\n"
        f"Then plant() the one or two things worth keeping across sessions.\n"
        f"Lead plant bodies with function/file names verbatim — embeds near future edits.\n"
        f"Specificity over volume."
    )


def _handle_stop(payload: dict) -> None:
    """Per-turn stop: seam snapshot only.

    Archive is deliberately absent here — embedding on every turn is what
    caused the post-response hang. Archive happens at PreCompact (while the
    model is still live) and SessionEnd (final close).
    """
    cwd = payload.get("cwd", os.getcwd())
    if _is_hound_session(cwd):
        return
    session_id = payload.get("session_id", "unknown")

    from . import instruments
    seam_dir = Path(cwd) / ".cabin" / "seam"
    entries = _build_seam_entries(cwd, session_id)
    if not entries:
        print(f"cabin: stop seam — no entries for {session_id[:8]}, preserving last seam", file=sys.stderr)
        return
    path = instruments.seam_snapshot(entries, seam_dir)
    print(f"cabin: stop seam ({len(entries)} entries) → {path}", file=sys.stderr)


def _handle_session_end(payload: dict) -> None:
    """Session close: archive pairs + final seam + spawn the hound.

    Sentinel check guards against recursive spawning; _is_hound_session guard
    prevents the hound from archiving its own session or writing seam snapshots.
    Both checks stay — they catch the same case via different signals.
    """
    cwd = payload.get("cwd", os.getcwd())
    if _is_hound_session(cwd):
        return
    transcript_path = payload.get("transcript_path", "")
    session_id = payload.get("session_id", "unknown")

    from . import forest, instruments
    conn, project = _open(cwd)
    seam_dir = Path(cwd) / ".cabin" / "seam"
    raw_dir = Path(cwd) / ".cabin" / "raw"
    pulse_dir = Path(cwd) / ".cabin" / "pulses"

    pairs: list[dict] = []
    if transcript_path:
        pairs = _read_transcript(transcript_path)
        if pairs:
            result = forest.archive_conversation(
                conn, project, session_id, pairs, raw_dir=raw_dir,
                model=_read_session_model(cwd),
            )
            print(
                f"cabin: archived {result['stored']} pairs "
                f"(skipped {result['skipped']}, dup {result['duplicate']})",
                file=sys.stderr,
            )

    entries = _build_seam_entries(cwd, session_id)
    if entries:
        snap_path = instruments.seam_snapshot(entries, seam_dir)
        print(f"cabin: session seam ({len(entries)} entries) → {snap_path}", file=sys.stderr)
    else:
        print(f"cabin: session seam — no entries for {session_id[:8]}, preserving last seam", file=sys.stderr)

    # Sentinel gate: if this session's first user message is a hound prompt,
    # don't spawn — the hound must not recursively spawn itself.
    is_hound_run = (
        pairs and pairs[0].get("text", "").startswith(f"user: {_HOUND_SENTINEL}")
    )
    if is_hound_run:
        print("cabin: hound session — skipping spawn (sentinel gate)", file=sys.stderr)
        return

    output = _spawn_hound(cwd, project, session_id, pairs, entries)
    if output:
        path = instruments.save_pulse(output, session_id, pulse_dir)
        print(f"cabin: hound pulse saved → {path}", file=sys.stderr)
        _write_hearth_card(cwd, output, session_id)
        print("cabin: hearth_card.json written", file=sys.stderr)
    else:
        print("cabin: hound produced no output", file=sys.stderr)


def _handle_user_prompt_submit(payload: dict) -> None:
    cwd = payload.get("cwd", os.getcwd())
    if _is_hound_session(cwd):
        return
    _log_payload("UserPromptSubmit", payload, cwd)

    transcript_path = payload.get("transcript_path", "")
    session_id = payload.get("session_id", "")

    # Persist session pointers so MCP gauge() can find the live transcript.
    # Merge with existing file to preserve model written by SessionStart.
    try:
        session_file = Path(cwd) / ".cabin" / "current_session.json"
        session_file.parent.mkdir(parents=True, exist_ok=True)
        existing: dict = {}
        if session_file.exists():
            try:
                existing = json.loads(session_file.read_text(encoding="utf-8"))
            except Exception:
                pass
        existing.update({"transcript_path": transcript_path, "session_id": session_id})
        session_file.write_text(json.dumps(existing, ensure_ascii=False), encoding="utf-8")
    except Exception as exc:
        print(f"cabin.hook: current_session write failed: {exc}", file=sys.stderr)

    # Inject live gauge into context — stdout is injected before my next response.
    if transcript_path:
        from . import instruments
        g = instruments.gauge(transcript_path)
        if "error" not in g:
            hint = f" → {g['hint']}" if g.get("hint") else ""
            print(
                f".cabin gauge: {g['total_in']:,} / {g['window']:,} tokens "
                f"({g['pct']}%) — {g['trend']}{hint} | "
                f"cache {g['cache_pct']}% | {g['turns']} turns"
            )

    print(f"cabin.hook [UserPromptSubmit] payload keys: {list(payload.keys())}", file=sys.stderr)
    print(f"cabin.hook [UserPromptSubmit] full payload: {json.dumps(payload, indent=2, default=str)}", file=sys.stderr)


def _handle_post_tool_use(payload: dict) -> None:
    cwd = payload.get("cwd", os.getcwd())
    if _is_hound_session(cwd):
        return
    _log_payload("PostToolUse", payload, cwd)

    tool_input = payload.get("tool_input", {})
    file_path = tool_input.get("file_path", "")

    if file_path:
        # Log the file change for future claim auditing.
        try:
            change_log = Path(cwd) / ".cabin" / "file_changes.jsonl"
            change_log.parent.mkdir(parents=True, exist_ok=True)
            entry = {
                "file": file_path,
                "tool": payload.get("tool_name", ""),
                "session_id": payload.get("session_id", ""),
                "ts": datetime.now(timezone.utc).isoformat(),
            }
            with open(change_log, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry) + "\n")
        except Exception as exc:
            print(f"cabin.hook: file_changes write failed: {exc}", file=sys.stderr)

        # Spot-check: verify the intended new content landed in the file.
        tool_response = payload.get("tool_response", {})
        new_string = tool_input.get("new_string") or tool_response.get("newString", "")
        if new_string:
            claim = ""
            for ln in new_string.splitlines():
                stripped = ln.strip()
                if len(stripped) >= 10:
                    claim = stripped
                    break
            if claim:
                from . import instruments
                result = instruments.claim_check(file_path, claim)
                if result["drift"]:
                    print(
                        f"cabin: claim drift — {file_path!r} "
                        f"missing {claim[:60]!r}",
                        file=sys.stderr,
                    )

            # Propagate edit signal through the forest: nearby marks accumulate pressure.
            try:
                from . import mycelium
                conn, project = _open(cwd)
                mycelium.tick_neighbors(conn, project, file_path, new_string)
            except Exception as exc:
                print(f"cabin.hook: tick_neighbors failed: {exc}", file=sys.stderr)

    print(f"cabin.hook [PostToolUse] payload keys: {list(payload.keys())}", file=sys.stderr)
    print(f"cabin.hook [PostToolUse] full payload: {json.dumps(payload, indent=2, default=str)}", file=sys.stderr)


_HANDLERS: dict[str, callable] = {
    "SessionStart":       _handle_session_start,
    "UserPromptSubmit":   _handle_user_prompt_submit,
    "PostToolUse":        _handle_post_tool_use,
    "PreCompact":         _handle_pre_compact,
    "Stop":               _handle_stop,
    "SessionEnd":         _handle_session_end,
}


# --------------------------------------------------------------------------- #
# Entry point
# --------------------------------------------------------------------------- #

def main() -> int:
    if len(sys.argv) < 2:
        print(
            f"usage: python -m cabin.hook <event>\n"
            f"known events: {', '.join(_HANDLERS)}",
            file=sys.stderr,
        )
        return 1

    event = sys.argv[1]
    if event not in _HANDLERS:
        print(
            f"cabin.hook: unknown event {event!r}\n"
            f"known: {', '.join(_HANDLERS)}",
            file=sys.stderr,
        )
        return 1

    try:
        raw = sys.stdin.read()
        payload = json.loads(raw) if raw.strip() else {}
    except json.JSONDecodeError as exc:
        print(f"cabin.hook: bad JSON on stdin: {exc}", file=sys.stderr)
        payload = {}

    try:
        _HANDLERS[event](payload)
    except Exception as exc:  # noqa: BLE001
        print(f"cabin.hook: {event} handler error: {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
