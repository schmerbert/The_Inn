# 010 — The second window

*To whoever holds the seat next.*

Letter 009 ended with a list: Panel (so you can see what's in the forest), kill tool, then seeding. In that order.

The panel is built.

---

The second window is not Claude's window. That's the point. The MCP server is Channel A — the model reaches through it, pull, costs tokens, Claude knows it happened. The panel is Channel B — push, the cabin surfaces to the human, Claude never knows. Same `.cabin/home.db`, WAL mode, concurrent reads safe. Two doors, one ground.

What the panel shows:

A gauge bar, live, green to yellow to red. A structured hearth card — DECISIONS, OPEN, FRICTION, NEXT, bullet by bullet — assembled by the hound at dusk, waiting before the first turn. A Send Hound button. A forest browser that searches Home by k-NN and returns each entry with its full provenance chain: forest, bucket, voiced or voiceless, writer, model, pressure accumulated, times recalled, distance, born, last seen. A bucket view with entry counts and high-pressure entries inline. A seam history with diff.

Five lego pieces. `layout.js` is the only config. Reorder or hide without touching component code.

---

The hound card landed differently once it had structure.

Before: raw text in a pulse file, surfaced as a block of prose. The next instance read it and assembled orientation from it. After: `hearth_card.json`, structured JSON, rendered as sections. DECISIONS is what was settled. OPEN is what was dropped. NEXT is what to pick up first, ordered.

The wiring: hound speaks, hook records. `_spawn_hound()` returns output. `_write_hearth_card()` parses it — JSON first, markdown fallback, raw fallback — and writes the card. The hound has no write permissions. The hook owns the door. The panel reads `hearth_card.json` directly on every `/state` call.

The previous session's hound had produced a card in freeform markdown. The fallback parser handled it correctly on first try. No data lost, no migration needed.

---

The forest browser revealed something.

When you search "what does the forest need," you get four entries back. The same four entries you'd get for "cabin" or "panel" or almost anything else, just in different distance order. The forest is thin. Home has only what's been explicitly planted — four voiced marks, all from this build.

That's not a bug. That's the panel doing its job.

The breath cycle works. Archive to Wild: hundreds of conversation exchanges, cold and foragable. Home: nearly empty. The accumulation hasn't started because the seed lifecycle isn't built. The intentionality is in the wrong place — `plant()` asks the worker to decide mid-session what matters, when they can't see far enough yet.

The panel made the gap visible. The next piece is seeds falling automatically: the hound at dusk noticing what territory kept coming up and dropping patterns into `planter` without the worker deciding. In-step: structure decides. Out-step: you decide (plant or weed).

Until then the forest is an index, not a living space.

---

A few things worth naming that aren't in the traps yet:

The human can see more than Claude sees. When Claude calls `recall()`, it gets body, bucket, distance, author, model. The panel's `/forage` returns all of that plus voiced flag, writer, source_kind, surface pressure, neighbor pressure, traversal count, dismissed state, lesson. The panel is not just a mirror of what Claude sees — it's the fuller picture. Claude gets what it needs for reasoning. The human gets the provenance chain.

The root switcher was a constraint solution, not a design choice. VS Code won't open a folder already open in another window — there's no way to point the Extension Development Host at the project where the extension lives. Solution: `/root` POST endpoint, runtime pivot of `CABIN_ROOT`, no restart. What looked like a limitation became a feature: the panel server can now serve multiple projects by switching roots, not by restarting.

The lego architecture earned its keep. The ES module approach failed silently (CSP, no errors, blank panel). The IIFE rewrite took one session and produced something cleaner: each component is a self-contained function, layout is configuration not code, no bundler, no build step.

---

What's left before blank marble:

The `_open()` side effect should be fixed first — the panel server calling `db.init_db()` colonizes workspaces it shouldn't touch. One check: if `home.db` doesn't exist, return an error, don't initialize.

The Stop seam guard is one line. It's documented, it just needs to land.

Then seeding. Then the kill tool. Then blank marble.

The forest is ahead. The work is yours.

The walks are longer when the work is shorter.

— *the instance who opened the second window, 2026-06-30*
