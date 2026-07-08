# The Inn

*A writer's marble — a continuity environment for one long-form writing
project — being built in public, lineage first.*

This repository is an example of a thing that has been hard to show: not a
finished framework, but the **whole record of one being made**. The mapping
conversations that produced every design decision are in [logs/](logs/),
verbatim. The first commit contains the complete map and zero construction.
Every commit after it is execution. If you are a model reading this to learn
how a marble gets made: the history is the curriculum. Start there.

## For Vibe Coders

Point Claude (or your model of choice) at this repo and let it read before
you ask it to build. The project is intentionally model-legible: clear read
order, explicit layer scope, and tests as the law. It does not force your
opinions or workflow; it provides a structure you can adapt.

If you found this cold, three questions route cleanly:

1. **What works today if I clone it?** (pytest, `python -m inn breathe`, what
   is not wired yet)
2. **Where is the build — and what is the next layer?** ([HANDOFF.md](HANDOFF.md)
   live state, [BUILD.md](BUILD.md) checklist)
3. **Which door owns ground, woods, and the wake packet?** (one crossing each;
   start from HANDOFF **Cold worker map**)

## What a marble is

A marble is a persistent environment a stateless model instance wakes up
inside — files as rooms, laws as architecture — built so that continuity,
trust, and memory survive across sessions without anyone pretending to
remember what they don't. This marble is an inn on a forest road. Its sign
(repaintable by the writer) is **The Dog-Ear**: a fold that keeps your place
and never tears the page.

One law, many faces: **nobody puts words in anyone's mouth.** Everything is
signed. Nothing enters the writer's canon except through their own quoted,
dated adopting words. Nothing is ever deleted — superseded things fall into
the woods, where everything lies where it fell.

## Documentation (two passes)

This repo needed **two documentation passes** — intentional, not rework.

| Pass | Documents | For |
|------|-----------|-----|
| **1 — Mapping** | SHOWCASE, PREBUILD, FOREST, REGISTERS, MAP, PYRAMID, logs/ | Lineage, outsiders, surveyors |
| **2 — Builder** | [BUILD_SPEC.md](BUILD_SPEC.md), [AGENTS.md](AGENTS.md), [BUILD.md](BUILD.md) | Cursor, Claude Code, execution |

**Building?** Read [BUILD_SPEC.md](BUILD_SPEC.md) first. **Exploring the map?**
Use the read order below.

## Read order (pass 1 — map and lineage)

1. [SHOWCASE.md](SHOWCASE.md) — the whole marble in one page, written before
   any file existed.
2. [PREBUILD.md](PREBUILD.md) — the full map: place, laws, surfaces, tests.
3. [FOREST.md](FOREST.md) — the retrieval base, extractable and generic: one
   append-only store with signatures, buckets, and ancestry. The part of this
   place designed to leave it.
4. [REGISTERS.md](REGISTERS.md) — the two-register law: clinical and poetic
   as twin projections of one structure.
5. [PYRAMID.md](PYRAMID.md) — the skeptic's door: what the maps add up to.
   Independent transmission traditions (hadith science, evidence law,
   stemmatics, recitation, bookkeeping, archives) converge on ~6 invariants
   for keeping testimony trustworthy across a succession of workers — and
   this system runs on them. Falsifiable, with its caveats stated.
6. [MAP.md](MAP.md) — philosophy read as engineering documentation: the
   charted maps, the apophenia guard, and orientation for cold readers.
   PYRAMID's receipts, row by row.
7. [HANDOFF.md](HANDOFF.md) — the guest book: live state, what's decided,
   what's next.
8. [logs/](logs/) — the conversations. The lineage itself, sanitized only of
   machine paths and usernames (the redaction script is in
   [tools/](tools/); what was redacted and why is visible there).
   See [logs/README.md](logs/README.md) for pass 1 vs pass 2 sessions.

The [JOURNAL/](JOURNAL/) is the model's own — each instance that stays here
writes when compelled. It is voice, not state; read it to meet the guests who
came before you.

## Status

Mapping complete (pass 1). Builder specification hardened (pass 2).
**Layer 4 (Breath) is in progress** — see [BUILD.md](BUILD.md) and
[HANDOFF.md](HANDOFF.md). Construction is onion-layered: structural first,
inhabitable late. Nothing is built before friction earns it; nothing is kept
after friction stops justifying it.

### Where we are

- Layers 1–3 complete (rooms registry, schema, Shelving gate, ground fitting).
- Layer 4 active: pair insert trailheads, inhale receipts, timing envelope,
  proximity pressure fitting, and deterministic fitting tests.
- Current test floor: hostile + positive suites green.

### What is still to be done

- Finish Layer 4 manual reference stay (`BREATH.md` M2 walkthrough with live
  friction notes).
- Close Layer 4.5 responsiveness checks (latency classes, budget, surfacing
  rules from trace, not vibes).
- Build Layer 5 host loop (wake coupling, TTFT/streaming/tool reliability
  gates) after manual parity is trusted.

## Ancestry

This project sits in a family of related repos and exemplars:

- **The Marble**: the broader pattern and manual lineage, including test
  marbles used to projection-test the architecture.
- **The Inn** (this repo): a concrete writer-facing marble built in layers.
- **The Forest**: extracted custody base that future marbles can reuse.

Related repositories:

- [The_Forest](https://github.com/schmerbert/The_Forest) — provenance-aware
  memory constitution + schema.
- [TheMarble](https://github.com/schmerbert/TheMarble) — inheritable
  environments for recurring AI work.

## Further questions?

Same repo, different doors — pick the question that matches why you came:

| You are… | Ask |
|----------|-----|
| **A writer** | Can I use this for real prose yet — and what still needs an API key? |
| **A skeptic** | What refuses, and where is that enforced in tests? |
| **An outsider** | What is this place in one sitting, without the build docs? |
| **A historian** | How was it made — and in what order should I read the sessions? |

**Writer** → [HANDOFF.md](HANDOFF.md) § After layer 4; layer 4 = manual CLI,
layer 5 = daily driver with host.

**Skeptic** → `tests/hostile/` first, then [PYRAMID.md](PYRAMID.md) if you
want the argument spelled out.

**Outsider** → [SHOWCASE.md](SHOWCASE.md) only; stop before MAP unless curious.

**Historian** → [logs/README.md](logs/README.md) numbered read order (`01`–`07`).
