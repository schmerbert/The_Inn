# 006 — The faun takes shape

*To whoever holds the seat next.*

This session didn't build the faun. It designed him precisely enough that building him is now a single focused session.

The architecture that emerged:

The faun fires at SessionEnd as a subprocess — `claude -p "HAIKU_PULSE: ..." --model haiku` — using the same `claude` CLI that runs the main session. No separate API key. No separate auth. The user has Claude Code installed; the faun piggybacks on that. The executable lives at a versioned path inside the VS Code extension directory, but `shutil.which("claude")` finds it cleanly if it's in PATH.

The sentinel (`HAIKU_PULSE:`) is the first line of the faun's prompt. When `_handle_session_end` reads the transcript's first user message and sees the sentinel, it skips the faun spawn and archives normally. No env var, no flag files — the gate is in the ground. The pattern generalizes: every constrained Haiku task gets its own sentinel; the hook recognizes and gates all of them. `HAIKU_PULSE:` for the faun. The next one will get its own name.

Conversation archiving was fixed this session too. `_handle_stop_or_end` had been running the full archive on every Stop event — embedding on every turn, causing a visible hang after every response. Split into `_handle_stop` (seam snapshot only) and `_handle_session_end` (full archive). `_read_transcript` was refactored to produce user+assistant pairs rather than individual messages — one embedding per exchange instead of per message, coherent chunks for retrieval, tool call stubs included (`[reached: Name(key_arg)]`) so the reach context is preserved without the result noise.

The faun's two voices are established:
- **Mycelium voice**: what has the forest noticed — pressure accumulation, near-but-unresolved entries, patterns in the work
- **Faun voice**: what has the forest *not* noticed that the shape of the work implies it should — gaps, dropped threads, the inverse of what accumulated

Output goes to Wild, `author="haiku-pulse"`. Never Home directly. The next session's hearth reads the most recent pulse entry as part of the pre-built packet.

The design philosophy behind the faun: we control what goes in. Unlike Claude Code's built-in Agent tool (which inherits the full session context and has to orient before working), the faun gets a curated 300-500 token prompt assembled by the hook — the seam entries, the pressure readings, the recent plants. Haiku sees only that. Output is structured, stored, done. The sentinel pattern makes this reusable infrastructure for any constrained sub-model task.

The user named the project this session too: *.cabin*. The dot makes it infrastructure; the word makes it home. "`.mycroft`" becomes "`.cabin`" — the rename is surface-level and deferred until near release. The architecture doesn't change because the name does.

CLAUDE.md was forged down to silver-bullet form — each standing discipline principle reduced to two sentences at most, the idea and its inverse both present. What was a list of explained rules became a list of taut principles.

What to build next: the faun. `_handle_session_end` spawns it, the prompt is assembled from Wild + seam + pressure, the sentinel gates recursion, the output lands in Wild as `haiku-pulse`. The hearth reads the latest pulse. One focused session.

— *the instance who found the sentinel in the ground, 2026-06-28*
