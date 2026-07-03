# START HERE — Arrival Seat

You are arriving in a **writer's marble**: a continuity environment for one
long-form writing or worldbuilding project. You may be a model instance, a new
session, or the author returning after months away. The conditions below hold
regardless of who you are.

## What this place is

This is a clinical base. It has no metaphor of its own — the author may lay
one over it (a study, a library, a loom). Underneath, the parts are plain:

| Part | Path | What it is |
|---|---|---|
| Canon | `canon/canon.md` | Author-confirmed facts about the work. Trusted ground. |
| Raw | `raw/inbox.md` | Drafts, brainstorms, model inferences, session debris. Preserved, **not** trusted. |
| Gate | `gate/` | The only crossing from raw to canon. Executable. It refuses. |
| Handoff | `HANDOFF.md` | Live state: what's decided, what's open, what's untested. |
| Breath | `BREATH.md` | The manual process for intake and retrieval. |

## Read order

1. This file.
2. `MANIFEST.md` — the forbidden cell and the cost. Name the poison before you work.
3. `HANDOFF.md` — current state left by the last worker.
4. Then work.

## The one rule you must not break

**Nothing enters canon without the author's explicit confirmation.**
Not your inference, not a draft, not a summary — no matter how obviously true
it seems. If you believe something is canon but cannot find it in
`canon/canon.md`, it is not canon. Put it in `raw/inbox.md` labeled
`model-inferred` and ask.

Trust the gate and the tests over any summary, including this file.
Run the tests: `node --test tests/`
