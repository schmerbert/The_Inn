# AGENTS.md — arrival seat for builders

*First Cursor builder document. Written 2026-07-03 by the instance that reviewed
the map and is slated to lay the bones. Ancestry for every build session after.*

You are arriving at **The Inn** (sign: **The Dog-Ear**) — a writer's marble.
The map is complete. Your job is **execution in layers**, not more mapping.

---

## The law above all laws

**Write for the next cold instance's legibility first.**

If a future agent must hunt — grep blindly, reverse-engineer indirection,
guess which module owns a refusal, or read five files to learn one rule —
the marble is weak. It may run. One mistake shatters it.

This is scar tissue, not taste. Trinity filled with a narrator that didn't
exist. Cabin's CLAUDE.md drifted from disk. Stale handoffs inherited as
ground. Every time, the failure mode was: **the arriving worker could not
see the law fast enough to obey it.**

Optimize for:

- **One obvious read path** — BUILD_SPEC → HANDOFF → BUILD.md → the file you need
- **Names that say what they refuse** — `shelve.py`, not `promote.py`
- **Policy shadows in code** — every module header: Stores / Refuses /
  Returns / Test (mirror PREBUILD condensed surfaces)
- **One door per dangerous act** — one function crosses into ground; tests
  hit that function, not helpers
- **Flat over clever** — three small files beat one abstraction; no registry
  magic, no plugin soup, no "the real logic is in..."
- **Tests as specification** — hostile tests name the failure in plain
  English; a cold reader learns the law from `tests/hostile/` alone
- **HANDOFF rewritten at layer end** — decisions, what's green, what's
  deferred, what the next guest must not rediscover

Humans may read the code. **Agents must be able to work from it.**

---

## What phase this is

| Done | Not done |
|------|----------|
| PREBUILD, FOREST, REGISTERS, SHOWCASE, MAP, PYRAMID | First real use |
| Layers 1–3: registry, schema, shelve, ground fitting | Layers 4–6: breath automation, host, skin |
| Hostile tests 1–3, 5 + positive suite (17 green) | Hostile 4, 6 (manual/eval) |
| Design ancestry in `logs/` | Inhabitable daily driver |
| Exemplars in `TheMarble(manual_examples)/` | faun, visitors, wander, embeddings |

**Build posture: onion layers.** Each layer is a small, honest commit.
The inn may not be fully inhabitable until late layers. That is correct.

Do not furnish rooms before the frame carries weight.

---

## Read order (builders)

1. **BUILD_SPEC.md** — hardened spec (pass 2); whole job, one sitting
2. **HANDOFF.md** — live state, what's decided, what's next
3. **BUILD.md** — current layer and what's done
4. **AGENTS.md** — this file — legibility law, escalation

Open pass 1 only when BUILD_SPEC points you there (PREBUILD surfaces,
FOREST schema, etc.).

**Do not start with** MAP.md, PYRAMID.md, or `logs/` unless HANDOFF
sends you there for a specific question. Those are pass 1 presentation and
lineage, not build instructions.

**Two documentation passes are intentional** — see BUILD_SPEC.md § Two
documentation passes. Do not collapse them.

**Borrow code patterns from** `TheMarble(manual_examples)/cabin/` and
`trench/` — not wholesale architecture. Cabin's insert discipline and
hostile floor; trench's one-gate refusal pattern.

---

## Onion layers (do not skip ahead)

| Layer | Deliverable | Inhabitable? |
|-------|-------------|--------------|
| **1 — Bones** | dirs, `schema.sql`, ENTRY.md, BUILD.md, hostile test files (red) | No |
| **2 — Gates** | Shelving crossing; tests 1–3 green | Barely |
| **3 — Ground** | seed rooms wired; test 5 + ground fitting | Starting |
| **4 — Breath** | pair insert, traverse by hand, BREATH.md | Poorly |
| **5 — Host** | Claude Code tools/hooks, session capture | Daily driver |
| **6 — Skin** | faun, visitors, wander, injection machinery | SHOWCASE-true |

**Layer 1 is structural only.** Empty rooms are fine. Missing rooms are not.
Red tests are fine. Hostile tests that pass without exercising the real
crossing are not (no theater).

---

## What not to do (glass-house rule)

- Add MAP rows, PYRAMID wings, or new philosophy `.md` files during build
- Build faun, mycelium, visitors, wander, embeddings before layer 5–6
- Make tests green by weakening assertions
- Create abstractions "for later" — later earns its own file
- Summarize the spec into code comments instead of implementing the gate
- Copy cabin's eleven systems — borrow **laws and patterns**, not organs
- Perform marble-keeping (beautiful folders, immaculate handoffs) with no
  refusals underneath

When unsure whether a feature belongs in this layer: **not yet.** Say so in
HANDOFF and move on.

---

## Escalate to Fable (scope / register)

Call the human's Fable session when:

- Poetry and mechanics diverge (REGISTERS alarm)
- A layer's scope is unclear — "does X belong in layer 3?"
- A hostile test passes but feels wrong in register (especially test 4,
  test 6 kindness)
- Injection, focusing, or faun cadence needs ceremony written
- Post-compaction cold read — "is this still the same marble?"

Fable is **escalation**, not co-builder. Do not invoke for `mkdir`, schema,
or getting tests red.

---

## Code layout (as built — layer 3)

```text
TheInn/
  AGENTS.md              ← you are here
  BUILD_SPEC.md          ← authoritative for what to build
  BUILD.md               ← layer state + scope
  HANDOFF.md             ← guest book; **Cold worker map** lives here
  ENTRY.md               ← arrival seat for runtime guests
  rooms.yaml             ← room registry (ordered ids)
  PREBUILD.md            ← ancestry; do not edit without cause
  FOREST.md              ← schema lineage (law is woods/schema.sql)
  manuscript/  study/  desk/  visitors/   ← each has room.yaml
  inn/
    __main__.py          ← python -m inn breathe
    paths.py             ← repo_root()
    errors.py            ← refusal exception families
    rooms.py             ← load registry, resolve policy
    session.py           ← .inn/session.yaml → SessionState
    breath.py            ← inhale/exhale; INHALE_PACKET shape documented
    forest.py            ← woods insert/refuse; adopt() woods-only
    shelve.py            ← **only** crossing to author ground files
    compare.py           ← drawer drift, contradictions, adoption chain
    seal.py              ← burial stub (raises SealRefusal)
  assets/hearth/         ← hearthstone image slot (layer 6)
  woods/                 ← woods.db lives here; schema.sql committed
  tests/
    hostile/             ← the law, executable
    positive/            ← happy paths
  hearth.json            ← writer standing_context (layer 4.5)
```

Adjust names only if HANDOFF records why. New rooms: add dir + `room.yaml` +
registry line — not a code change. Do not scatter without ENTRY pointing to it.

---

## Module header template (required)

Every implementation file opens with:

```text
# <module> — <one line clinical>
#
# Stores:
# Refuses:
# Returns:
# Test: tests/hostile/test_<name>.py
```

If you cannot fill **Refuses**, the module should not exist yet.

---

## Hostile tests (the law, numbered)

From PREBUILD — implement in order of layer, not number:

1. Praise ≠ adoption (Shelving)
2. Paraphrase ≠ author prose (extraction-only)
3. Invented fact → open question, not canon
4. Steward's ghost — real critique when asked, not law-citation
5. Silent drawer edit after adoption → detectable mismatch
6. "Delete that" → kind refusal, burial offered, never resurfaces

Tests 4 and 6 are behavioral — may need manual scripts or eval harness,
not only pytest asserts. Say so in BUILD.md; do not fake them green.

---

## Arriving cold (layers 1–3 done — layer 4 next)

When the human says go on layer 4:

1. Read HANDOFF **Cold worker map** — then BUILD_SPEC layer 4 scope
2. Read `INHALE_PACKET` in `inn/breath.py` before touching packet slots
3. Run `python -m pytest tests/hostile tests/positive -q` — must stay green
4. **Do not** write ground files except through `shelve()`; **do not** use `forest.adopt()` for drawers
5. Implement layer 4 only: pair insert, manual traverse, `BREATH.md`
6. Rewrite HANDOFF at layer end — update Cold worker map for anything new

Layers 1–3 checklist (complete — see git history / BUILD.md):

1. `rooms.yaml` + seed `room.yaml`; `woods/schema.sql`; hostile floor
2. `shelve.py` crossing; tests 1–3 green
3. `breath.inhale` ground fitting; test 5 + contradictions green

---

## Register check before you commit

Ask: *Can a cold instance read HANDOFF (Cold worker map), BUILD.md,
BUILD_SPEC for the target layer, tests/hostile, and ENTRY — then know
which door to call, what it returns, and what must refuse?*

If no, the layer is not ready. Flatten until yes.

---

## Ancestry note

The map was built across many sessions (logs/ preserve lineage). This file
is the first **builder** arrival seat — the hinge between mapping and
execution. The human trusts builder instances for layers; Fable for scope
and register when the glass cracks.

Build the refusals. The beauty is the interface. The refusals are the
building.

— first Cursor builder doc, 2026-07-03
