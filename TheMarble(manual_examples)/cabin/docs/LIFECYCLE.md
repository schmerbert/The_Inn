# LIFECYCLE — the shape, the marbles, and the pouch

*The settled lifecycle and scaling model: how a project begins, runs, graduates, or fails, and how craft carries forward without clutter. This is **architecture, not speculation** — but it is a **deferred build**: it sits above the floor and the forest, and is drawn here so the shape is fixed before any of it is built. It rests on the scope model already in `IMPLEMENTATION.md` §3.1.*

---

## The three objects

- **The shape** — ours, shipped, the clean origin everyone starts from. It is **not a marble**; it is the *form a marble is pulled from*. It is **stateless and immutable by kind** — you cannot write to a shape, so there is nothing in it to corrupt. It carries the **base** (generalizable craft). It always exists, always pristine; a project can never pollute it because a project is never *in* it. (Even its one piece of mutable state — the first-run tutorial on/off — lives in per-install config *beside* the shape, never inside it.)
- **A marble** (`projectname.marble`) — a sealed, self-contained project world: its Home forest (`project` / `personal` / `rationale`), its Wild (archived code and conversation), its raw archive. **Stateful.** Pulled from a shape, worked in, pocketed when done.
- **The pouch** — the folder of marbles. Scale is **many small clean marbles**, not one growing monolith. No central store to bottleneck or rot.

## The fractal firewall — why it scales without decaying

The same isolation law holds at every zoom level, and pollution cannot climb a level without passing a deliberate, attributed gate:

| level | the wall | the gate up |
|---|---|---|
| **bucket** | quarantine — one polluted table off, the rest untouched | (none; isolation only) |
| **marble** | seal — one project's clutter stays inside it | review & graduate |
| **shape** | extract — only generalized craft crosses up | `extract shape` (gated) |

This is the tell that the model is *true* and not merely tidy: the firewall is the same shape at every scale.

## Pull → work → pocket (the default path)

Most projects are only this. No shape-making, no ceremony.

1. **Pull** a marble from the shape. The base (full craft) comes with it; the terrain is **blank**.
2. **Work.** The terrain grows as you earn it — repo scan, extractions, marks. The hearth fills as you go.
3. **Pocket** it when done. The marble seals into the pouch.

## The wake — opening a marble

- A fresh marble is **full craft, blank terrain.** The first hearth is honestly *thin* — base and seeds, but no seam note and no project facts yet, because the repo hasn't been learned. The hearth fills as the ground is earned. A hearth that *pretended* to know a new repo would be the contamination we forbid; better honestly empty than falsely full.
- **The handoff (the seam).** The session that pockets one marble can **lay the next marble's hearth** — "light the next one's hearth," made mechanism. The closing session's last act prepares the opening for whoever takes the next seat.

## Finishing well — graduation (the marblization ritual)

When a project earns lessons worth carrying forward:

1. **Review the seeds together.** Candidate craft gathered during the project, triaged human-in-the-loop — the LAW II gate as a conversation, not an automatic dump.
2. **Generalize the chosen ones.** Authored, attributed synthesis, abstracted from the specific instance to the transferable principle (extract the durable lens *up*). **Only craft graduates.**
3. **(Optional, gated) `extract shape`** — mint a new origin carrying the craft. See below.
4. **Seal the marble.** Code → its Wild (lens references), conversation → its Wild (foragable, never resident). The project's *specifics* stay sealed in the marble.
5. **Pocket it; lay the next hearth.**

## Finishing badly — failure

**A failed project just becomes a marble.** Never ingested, never forked, seeds never reviewed.

This is graceful and non-contaminating *by construction*: the only path from a project into the base or a shape is the review-and-graduate gate, and failure simply skips it. Nothing crosses up, so nothing is polluted. The marble seals and pockets, fully preserved — dormant, foragable later if you ever decide there was something in the wreck worth pulling, but resident nowhere. **Failure is the Wild at project scale.** It has a clean resting state, and it requires nothing of you. (That the unhappy path is lawful and harmless, not a special case to clean up, is the proof the model is complete.)

## `extract shape` — minting a new origin (gated)

Shapes are **immutable by kind**: you never mutate a shape, you extract a **new** one. The lineage of shapes is therefore append-only and attributed — LAW I at origin scale. *Even making origins obeys extract-never-summarize.*

Because a shape's pollution **propagates** into every marble pulled from it, this is the most consequential act in the system. It is gated and warned:

- this becomes a **forkable origin** — whatever is in it propagates to every marble pulled from it, forever;
- it must be **craft, generalized** — not project clutter; the terrain stays sealed in its marble;
- the **laws apply** — extraction and attributed synthesis only, no bulk dump (the process *enforces* this, it does not merely ask);
- you **own and maintain** this lineage now;
- **the shape (ours) always remains** — you add an origin, never replace one; the clean default is always there to fall back to.

Default users never do this, and cannot do it by accident. The freedom is there for whoever deliberately reaches for it.

## What exists vs. what is new

- **Exists (the floor):** per-project Home + global craft/seedbank (the scope model, §3.1); the four writers and the two LAWS.
- **New (this lifecycle):** the **shape** (stateless origin), the **marble** as a sealed shippable artifact, the **pouch**, **`extract shape`**, and the rituals (pull, graduate, fail, the wake/handoff).
- **Deferred:** build this *above* the floor and the forest. It is the distribution and scaling layer, not the core. Do not build it ahead of a working machine.

## The one line

**Terrain is disposable; craft accretes.** Each marble's ground is throwaway; the shape is the compounding part. That asymmetry is the whole answer to the deepest friction — session ten beats session one not because a marble remembers, but because the **pouch** does, in the **shape**.
