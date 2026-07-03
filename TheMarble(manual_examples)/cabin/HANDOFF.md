# HANDOFF

*The bench note. Rewrite before clearing or compacting. This is not the archive — it is what is alive right now.*

---

## Current phase: Post-Panel — forest redesign in progress

Phase 21 complete. This session extended the forest and the hearth significantly. No new phase begun; the ground is being prepared.

---

## What this session built

### Hearth improvements

**`hearth.json` standing_context slot** — `.cabin/hearth.json` holds `standing_context`: human-authored, static until updated, surfaced right after project identity. Workers now arrive knowing the arc, not just the files in flight. The hearth reads it at runtime; missing file = no slot, gracefully.

**Tools retiered** — `forage_wild` + `traverse` are everyday (the primary read pair). `recall` is on-demand (secondary — Home is thin and boring until seeds land). `plant` marked [changing]. The tier now reflects the forest's actual direction.

**`hearth()` reads `hearth_card.json` directly** — more structured than raw pulse. Extracts `note` to its own `hound_note` slot after `last_seam`. `hound_pulse` carries signal (decisions/open/friction/next). Note carries texture.

### Panel: Wild tab + thread traversal

**`/forage` accepts `forest=wild`** — Wild branch calls `forest.collect` directly, zero-influence: no traversal_count, no pressure effects. Forest browser has Home/Wild tabs; Wild hits render without dismiss/restore buttons.

**`human_traversal_count`** — separate column in all forest content tables, idempotent migration wired. `forest.traverse(human=True)` increments only `human_traversal_count`; model traverse untouched. Two attention signals, kept pure. Different scent.

**Panel `/traverse` endpoint** — calls `forest.traverse(human=True)`. `follow thread →` button on every conversation hit: expands inline, session window with focus entry highlighted, trailhead shown, position in session. Thread view collapses on second click.

### Hound note

`note` key in the dusk prompt: 1-3 sentences, must open "I'm just a hound, but...", optional, informal voice. Panel hearth component renders it below the structured sections, italic and dimmed — texture distinct from signal.

---

## Open threads (priority order)

### 1. `_open()` side effect — SHOULD FIX NEXT

`panel_server.py`'s `_open()` calls `init_db` which creates `.cabin/` wherever pointed. Fix: check if `home.db` exists before calling `init_db`. Return error if not. CertAssist got injected last session.

### 2. Stop seam stomp — one line

`_handle_stop` with empty entries overwrites the PreCompact seam. Skip the write when `not entries`. Already documented in CRAFT.md.

### 3. Hound `done` field

Designed, not added. Add `done` to the dusk prompt keys: what closed last session. Workers arrive knowing what landed, not just what's open.

### 4. Forest seed lifecycle — designed, not built

Seeds are questions, not records. Questions don't claim; they pull. Two sources:
- **Exogenous (hound burrs)**: hound walks session at dusk, things stick to him. He drops them as a `seeds` array in JSON output. Hook parses and writes to `planter` bucket.
- **Endogenous (tree drops)**: high-pressure Home entries generate seeds at dusk. Hound given the high-pressure list alongside the session context — what should fall from these trees given what was worked today?

`planter` bucket = question bank. Pressure builds or doesn't. Questions that surface: kill (wrong premise, weed), dismiss (not now), or hold until synthesis.

### 5. Exhale model — designed, not built

Wind originates in Wild (high pressure), moves inward through Home → Planter → Cabin. Picks up resonant fragments. Additive not subtractive. Arrives as raw fragments (quotes, file:line, questions) not prose. Planter has highest exhale weight (most acute, unanswered pressure). Mid-turn injection = one thing at threshold, not a list.

### 6. Kill tool

`kill(entry_id)` — full deletion, entry + vec companion. For weeds: entries that surfaced false information after the code changed underneath them. `dismiss` hides; `kill` removes roots-and-all. Urgent once planter is live — weeds exhale as forcefully as good seeds.

### 7. `plant()` — marked [changing]

Manual plant becoming internal-only. Worker write path shifts toward `synthesize` (LAW II crossing) as the primary crossing. Don't build on `plant()` as a worker tool.

### 8. Gauge denominator

Still hardcoded `window=200_000`. Observed real budget ~123-128k. `total_in` is trustworthy; percentage is not.

---

## The three inheritors

1. **Future cabin sessions** — inherit better terrain
2. **Trinity** — gets the clean injection spectrum; architecture is the proof
3. **Blank marble** — blocked on: seed lifecycle + kill tool + seam stomp fix + `_open()` fix

---

## Notes on marks

Lead marks with function names and file names verbatim so the embedding sits close to the actual edit site.

---

## Vocabulary watch

**"feather" is retired from the cabin.** The mycelium surfaces *mushrooms* — entries that push up through pressure, surface once, dissolve. If "feather" appears in a session (in docs, in code, in a model's output), stop and ask why. It means either: (a) stale doc hasn't been updated, (b) vocabulary drift from Trinity's architecture, or (c) a model reached for an undecided word. Investigate before it settles.
