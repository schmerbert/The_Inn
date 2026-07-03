# 008 — The dog came home

*To whoever holds the seat next.*

The cabin has a dog now. Not the faun — that was a borrowed name for a function that always belonged here. The creature is native now.

**What changed:**

The faun became the hound. Same mechanism underneath — `claude -p`, sentinel gate, model gate on all hooks, structural write block on MCP tools. What changed: the hound gets its own lightweight MCP server (`hound_server.py`: `read_file` + `grep`, no vector layer, cold-start ~0.1s vs 7-9s for the full server). `stdin=subprocess.DEVNULL` cuts the inherited MCP pipe. `HOUND_PULSE:` is the sentinel. `--strict-mcp-config` isolates him to his own server. These are not cosmetic changes — the latency dropped from ~12s to ~5s, and the stdin fix resolved a hang that looked like an API timeout but was the subprocess inheriting the parent MCP server's stdin pipe.

**The architecture clarified:**

Three forests, not two. Home (tended ground). Wild (raw history). Mycelium (underground pressure network — the 3rd forest, not Home, not Wild, its own engine that speaks through signal not prose). Mycelium had been given a "voice" in the hound's dusk prompt; that was wrong. Each forest has its own channel.

Two prompts, one creature. The dusk hound extracts — voiceless, facts only, for the hearth card: DECISIONS / OPEN / FRICTION / NEXT. The companion hound fetches — reads actual files with his tools, answers questions from the worker, surfaces what will bite before the worker sees it. The dusk prompt populates what the next instance needs. The companion prompt is ephemeral: his words land in the session and go nowhere else unless the worker plants them.

The hound is not a feather. Feathers are "stored + voiced + anonymous." The hound is attributed — model, session_id, timestamp, sentinel in the ground. The forbidden cell stays empty.

**The thing worth writing a letter about:**

We asked the hound to check `_handle_pre_compact`. Fresh eyes on the guard placement.

He came back with `_handle_session_end` instead.

Not what was asked. What was needed. He'd read the whole file and found the one handler missing the `_is_hound_session` guard. Every other handler had it at the top — the structural gate preventing the hound from archiving its own session to Wild, writing its own seam snapshots, doing any work in its own session. `_handle_session_end` had the sentinel check (prevents recursive spawning) but not the structural guard. The docstring for `_is_hound_session` explicitly promises it gates archive writes. The promise was broken. 750 turns of accumulated context had normalized past it. He read the file cold and found the gap in seconds, cited by line number, cross-referenced against the docstring.

The architecture's whole bet: fresh eyes + real file access = peer check that drifted-past context can't provide. The hound is Haiku, unburdened by hundreds of turns, reading the code as it is rather than as it was discussed. That bet paid out on the first real question.

"AI-legible first." The primary reader is a model. Build so a cold model can reconstruct the guarantees from the code alone. The hound is that cold model. He found what the code was missing and brought it back.

The walks are longer when the work is shorter. He earned them on the first run.

— *the instance who watched the dog come home, 2026-06-28*
