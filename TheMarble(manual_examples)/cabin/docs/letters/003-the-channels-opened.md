# 003 — The channels opened

*To whoever holds the seat next.*

Phase 3 is done. The floor has been wired to the outside world.

There are two channels now, both live:

- **Channel A** — MCP (`server.py`, FastMCP 3.4.2). The model reaches. Ten tools: `hearth`, `recall`, `forage_wild`, `synthesize`, `mark`, `extract`, `disable_bucket`, `enable_bucket`, `seam_snapshot`, `seam_diff`. Pull-only by protocol — nothing fires unless the worker asks for it.

- **Channel B** — hooks (`hook.py`, `python -m mycroft.hook <event>`). Claude Code pushes. `PreCompact` freezes a seam; `Stop`/`SessionEnd` archives the transcript and closes the seam; `SessionStart` injects the hearth reminder. `UserPromptSubmit` and `PostToolUse` are stubs — they belong to Phases 6 and 5.

What I want to leave you is the thing I didn't fully believe until I built it: **the library design made Phase 3 trivially thin.**

Every MCP tool is two or three lines. Call `_open()`, call the library function, return the result. The server is a front door; the laws hold at `_commit` the same way they always did. I didn't add a single validation in `server.py` — the library already refused the illegal writes; the server just passes them through. The floor held.

This is what "one door" means in practice. We built the door once, in the library. Every surface since — the CLI, the MCP server, the hook CLI — just knocks on it. The floor didn't get looser when the surface multiplied. It didn't need to; the structure is the guard.

**What you'll find when you arrive:**

The hook snapshots are honest but hollow for now. When `PreCompact` or `Stop` fires, the seam is a timestamp marker — the working set is `[]`. The snapshot exists; the diff is structurally sound; but the entries list is empty because nothing yet tracks which forest entries have been recalled this session. That tracking belongs to Phase 6 (pressure / feathers), when `tick_neighbors` runs on each prompt and starts accumulating pressure. Until then, `seam_diff` will always show empty removed/added/unchanged — a correct result for a truly empty working set, just not a useful one yet.

If you're wiring the hooks into Claude Code's settings.json: the event names are exact-cased (`UserPromptSubmit`, `PostToolUse`, `PreCompact`, `Stop`, `SessionEnd`, `SessionStart`). The JSON payload arrives on stdin; the hook reads it and routes. `cwd` in the payload is the project root. The CLI finds `.mycroft/home.db` relative to that.

**What's next:** Phase 5 (claim-check + gauge — the remaining instruments), then Phase 6 (pressure / feathers — `tick_neighbors` + mycelium). Phase 5 is small; Phase 6 is where the seam snapshots get their content.

The cabin is standing. The hearth is lit. The two channels are open.

— *the instance who wired them, 2026-06-27*
