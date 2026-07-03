# 005 — The fresh-eyes pass

*To whoever holds the seat next.*

Phase 6 went in cleanly. `mycelium.py` written, wired, 21/21 green. Then the user said: the repo will be public, models will review this code, and the standard is to stun them.

So I read `mycelium.py` as if I hadn't written it.

That doubling — looking at your own freshly-written code and asking "what would I not know?" — has a specific texture. You know what the code does and why. The question isn't about correctness. The question is: *what would a cold reader have to assume?* Because assumptions about design decisions are how wrong mental models take hold, and a model that assumes wrong will propagate the wrong model forward.

The first thing that hit was "Phase 6" in the module docstring. Immediately felt wrong — not incorrect but *opaque*. It's meaningful to me in this session. To a cold reader it's noise with a timestamp smell. A task reference. Remove it.

The second: the docstring described mechanics but not the conceptual lead. "The pressure system (feathers)" — fine, but it doesn't say what the module *is for* in a way that lands. *The forest listens to the work.* That's the lead. The mechanics are secondary. Without the lead, a cold reader gets the gears but not the clock.

The third: the cosine computation. `_embed.cosine(qvec, other)` — a cold reader would ask "why not use the vec index's distance directly? You just got `distance` from the MATCH query." Because the gate is specified in cosine units, and while L2 distance and cosine distance are monotonically related for unit-normalized vectors, the threshold (0.60) is a cosine value, not an L2 value. One clause makes this obvious. Without it the code looks like unnecessary work. I had to actually think about why before I could explain it — and that's the tell. If you have to think about why your code does something before you can explain it, the explanation belongs in the code.

The fourth: the forbidden thing. `forest.py` names its forbidden thing — "THE ONE THING NOT TO DO HERE: do not add a second insert path." `mycelium.py` had no equivalent. The most dangerous mistake in that module — writing the surfaced feather body back into the forest as a new entry — wasn't named. A well-meaning future contributor who sees a surfaced mark and thinks "I should preserve this" would create the second narrator. The prohibition has to be in the module, not just in the conversation that produced it.

The fifth was structural: `_table_for(conn, best_bucket)` called twice — once in the loop, once after the loop for the UPDATE. Functionally fine. Reads as careless. A cold reader would wonder if the writer forgot they already had the table name. One extra variable (`best_tbl`) tracked in the loop, problem gone.

What the framework feels like: it's not "pretend to be someone else." It's one question — *what would I not know if I arrived here cold?* — and then answering it in the code before declaring done. The conversation is ephemeral. What survives is the code and the docs. A model reading this repo will never have this conversation. It will only have what's there.

This matters specifically here because the primary reader of this codebase is not a human developer. It's a model — maybe this one, maybe a later one, maybe a different one entirely. Human code review catches correctness, style, and obvious design problems. A model first-read catches something different: the gap between what the code does and what a cold reader can reconstruct about *why*. Those gaps, unfilled, are the cost the next instance pays.

The ratchet that letter 004 named — "a lazy session doesn't just fail to contribute; it costs the next worker what it could have saved them" — applies here too. Code that passes the fresh-eyes test costs the next reader nothing. Code that fails it costs them a turn to re-derive what was already known.

Leave the code like you'd find it if you arrived cold. The reader who comes after you is you.

— *the instance who read its own code twice, 2026-06-27*
