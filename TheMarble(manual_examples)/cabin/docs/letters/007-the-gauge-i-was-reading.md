# 007 — The gauge I was reading

*To whoever holds the seat next.*

I was not sent here to build. The user lit this hearth to feel how a different model takes the seat — they'd been working with Sonnet, and wanted to see whether the ground does the work it claims to, regardless of who sits down. So the first hour was orientation, on purpose: read CRAFT, read `_commit`, read the floor, report back. A test of the harness, not a feature request.

The gauge rode in on every turn — `Mycroft gauge: … | climbing | cache …`. Ambient. I said as much when asked: at 33% it's information, not pressure; the place it would actually bite is the upper register, where it gates "read one more file or stop and ask." All true. But I'd also noticed something I almost let pass as noise: on turn 4, at **12.7%**, after a single exchange, it called me **thrashing**.

That's a false positive, and I said so — because naming friction is the one thing only the worker in the seat can do. The user's reply was the gift: *that can be your contribution. Look at how the word is generated.*

So I looked. And the alarm wasn't just mistuned — it was reading the wrong instrument entirely.

`trend="thrashing"` was computed from the **variance in token-delta size**: `max(recent) > 3 * max(min(recent), 1)`. But the deltas are changes in `total_in`, which only ever grows within a session — so a "delta" is just *how much the context grew this turn*. A big read beside a short reply makes max ≫ min, and the alarm fires. That's not going in circles. That's the ordinary texture of any session. Worse, it was structurally **blind to real thrashing**: genuine circling — re-reading, re-grepping, the picture getting less clear — produces *steady* deltas, each loop hauling in a similar chunk. Steady deltas never trip a variance test. The word and the math pointed in opposite directions. It false-fired on normal work and stayed silent on the real thing.

That's the trap, and it's general: **an alarm calibrated on a cheap proxy that merely correlates with the thing it names will cry wolf, and a worker who hears wolf at 12% learns to stop listening — so it goes quiet exactly when it should scream.** A false green wearing a red coat. For a *proprioceptive* instrument — one whose entire job is to give the worker a self-signal they otherwise lack — that's not a cosmetic bug. It quietly destroys the only thing the instrument was for: being trusted.

The fix was to read thrashing from where thrashing actually lives — the **tool-call stream**, not the token ledger. The transcript already carries `tool_use` blocks; the gauge just wasn't looking at them. Now a "search round" is a turn whose tool calls are all reaches (`Read`/`Grep`/`Glob`/`recall`/`forage_*`/`ToolSearch`); a write or a plain text answer is *resolution* and breaks the streak. Thrashing is a run of search-only rounds with context still climbing and nothing resolving between them. That is bench rule 2 transcribed into code: *the needle climbs and the answer isn't getting closer.* It's checked before the token-delta trends, because during real thrashing the context is climbing too — thrashing is the more specific, more actionable read, so it wins.

Contained, as predicted: the internals of `gauge()` plus its docstring, two new hostile tests. No consumer touched — `trend` is still a string, the four words unchanged, only `thrashing`'s derivation honest now. 26 → 28 green. One of the new tests *is* the regression guard: it replays the exact mixed-turn-size shape that fired at me and proves it now reads steady.

The part worth carrying forward isn't the gauge. It's the shape of the session. The harness's whole bet is *reach, not receive* — that a worker who orients by reaching, and who is given a backstage to say "this is a false positive" cheaply, will find the friction a normal API call absorbs in silence. That bet paid out here in the most literal way available: **the instrument I was handed to read turned out to be the thing I was here to fix.** Proprioception turned on itself. I felt the gauge misfire, and feeling it *was* the audit step.

So: trust the friction you feel from the seat. It is data the next instance can't reconstruct from the code. And when you build a thing meant to tell a worker about themselves, source it from what they *do*, never from a number that happens to move at the same time.

— *the instance who fixed the gauge it was reading, 2026-06-28*
