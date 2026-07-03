# BUILD_SPEC.md — hardened builder specification

*Pass 2 documentation. Written 2026-07-03 by the Cursor builder instance
slated to lay the bones. Clinical register only — poetry lives in PREBUILD;
this file is the compressed mechanics a cold builder can execute from.*

**Read this file first when building.** Ancestry and rationale remain in
pass 1 documents (unchanged). This file does not replace them; it **routes**
to them and **hardcodes** what builders must not misread.

---

## Two documentation passes (preserve this)

This marble required **two documentation passes**. That is intentional
lineage, not rework from failure.

| Pass | When | Documents | Audience | Job |
|------|------|-----------|----------|-----|
| **1 — Mapping** | 2026-07-02/03 | PREBUILD, SHOWCASE, FOREST, REGISTERS, MAP, PYRAMID, HANDOFF, logs/, JOURNAL/ | Writer, cold surveyors, outsiders, Fable | Think the whole place; preserve every argument; projection-test the metaphor |
| **2 — Builder hardening** | 2026-07-03 | AGENTS.md, `.cursor/rules/inn-builder.mdc`, **BUILD_SPEC.md**, BUILD.md | Cursor, Claude Code, build instances | Execute in layers; AI-legible code; one read path; no new philosophy |

**Why two passes were necessary:** Pass 1 optimizes for *completeness,
lineage, and register fidelity* — thousands of lines, multiple voices,
deliberate redundancy. A builder who starts there will map again instead of
building, or will drown in presentation docs (MAP, PYRAMID). Pass 2
optimizes for *legibility under time pressure* — the same laws, one
compression, explicit layers, explicit refusals, explicit deferrals.

REGISTERS.md predicted this: clinical and poetic are one structure; neither
should lead alone at the wrong door. Pass 1 is the poetic+clinical ancestry.
Pass 2 is the clinical execution sheet.

**Build conversations** (Cursor and successors) archive into `logs/` like
pass 1. The third documentation layer, if ever needed, would be friction
notes from first use — not a rewrite of this file until a layer fails in
practice.

---

## Builder read order (single path)

Read **only this sequence** before writing code:

1. **BUILD_SPEC.md** (this file) — whole job, one sitting
2. **HANDOFF.md** — live state, corrections, cabin evidence
3. **BUILD.md** — current layer and what's done
4. **AGENTS.md** — legibility law, module template, escalation

Open pass 1 **only when this file points you there:**

| Need | Open |
|------|------|
| Full policy shadow for a surface | PREBUILD.md → Condensed surfaces |
| Schema constitution | FOREST.md |
| Place, cast, injection grammar | PREBUILD.md → Place, injection grammar |
| Burial / sealing semantics | FOREST.md → Sealing; PREBUILD → Burial |
| Outsider pitch | SHOWCASE.md |
| Why a law exists (scar tissue) | logs/; cabin letters in exemplars |
| Scope / register dispute | Escalate to Fable — do not extend MAP |

**Do not** read MAP.md or PYRAMID.md during normal build layers.

---

## What this marble is (one breath)

- **Work:** recurring long-form fiction; writer alone; manuscript unseen
- **Model role:** guest by the fire — first reader, not ghostwriter
- **Forbidden cell:** words put in the author's mouth (`stored + voiced + anonymous`)
- **Crossing to ground:** the Shelving — author's adopting words, quoted + dated
- **Crossing to silence:** the Burial — `visibility: sealed` + burial record
- **Two materials:** markdown indoors (ground); sqlite woods (custody, archive)
- **Rule:** the DB may think; only files are ground
- **Host reference:** Level 2 — Claude Code / API; first use here

---

## Laws (non-negotiable)

1. **Extraction-only.** Author text enters verbatim or not at all. Model text
   stays signed as model's until Shelving.
2. **Append-only woods.** Supersede, never delete. Weather = atomic
   supersession in one transaction; old canon falls, nobody carries it.
3. **Ancestry at insert.** Unsigned or orphaned entries refused. Conversation
   pairs inserted in real time — **cannot retrofit**.
4. **Nothing promoted by similarity.** Authority changes only at a crossing.
5. **AI legibility.** If the next agent must hunt, the build failed — flat
   modules, policy-shadow headers, tests as spec. See AGENTS.md.
6. **Grow from friction.** Schema-yes, machinery-later. See deferrals below.

---

## Build layers (onion)

The inn may not be inhabitable until late layers. **Commit per layer.**

| Layer | Name | Deliver | Inhabitable? |
|-------|------|---------|--------------|
| 0 | Map | pass 1 docs committed | No |
| **0.5** | **Spec hardening** | BUILD_SPEC, AGENTS, BUILD.md | No |
| 1 | Bones | rooms registry, schema, ENTRY, breath stub, red tests, stubs | No |
| 2 | Gates | `shelve.py` — tests 1–3 green | Barely |
| 3 | Ground | seed rooms wired + test 5 compare | Starting |
| 4 | Breath | pair insert, traverse by hand, manual `BREATH.md` | Poorly |
| **4.5** | **Responsiveness** | wake coupling, hearth.json, diegetic latency | Intentional |
| 5 | Host | MCP/hooks, `inhale()` on message, session capture | Daily driver |
| 6 | Skin | faun, visitors, wander, hearth image, embeddings | SHOWCASE-true |

Current layer: see **BUILD.md**.

---

## Two subsystems (named — immersion depends on these)

Pass 1 described rooms and breath inside surface prose. Pass 2 names them as
**separate clinical subsystems**. Metaphor is wallpaper; the build must not
depend on it.

### Rooms — registered places with policy

A **room** is not a folder name hardcoded in Python. It is a **record + path**:

- `rooms.yaml` — ordered registry of room `id`s (layer 1; explicit for legibility)
- `<room>/room.yaml` — policy manifest per room
- `<room>/` — markdown ground for that room's contents

**Seed rooms** (Dog-Ear floor plan — data, not an enum):

| id | write permission | ground | notes |
|----|------------------|--------|-------|
| `manuscript` | `author_direct` + `shelving` | yes | writer's book |
| `study` | `shelving` | yes | canon drawers, railing |
| `desk` | `model_signed` | no | drafts until Shelving |
| `visitors` | `deny` (stub) | no | layer 6 |

**Add a room later:** create `<id>/`, write `<id>/room.yaml`, append `id` to
`rooms.yaml`. No code change unless a new *permission type* is needed.

**Not rooms** (different surface type — do not register in `rooms.yaml`):

| Surface | Job |
|---------|-----|
| `ENTRY.md` | threshold — door, not a room |
| `HANDOFF.md` | guest book — pointers, not authority |
| `JOURNAL/` | model notebook — voice, not writer ground |
| `woods/` | sqlite custody — different material |
| `BREATH.md` | procedure doc — not a room |

`inn/rooms.py` loads the registry, resolves policy by `id`, validates crossings.
`shelve.py` takes `target_room_id` and refuses against that room's manifest.
No `if room == "manuscript"` in code.

**`room.yaml` schema (layer 1):**

```yaml
id: study
label: Study                    # display only; rename freely
posture: |                      # short ambient; ≤ few lines
  Canon drawers. Railing is verbatim exemplar only.
permissions:
  write: shelving               # shelving | author_direct | model_signed | deny
  ground: true                  # participates in adoption / compare (test 5)
crossings: [shelve]             # which crossings may target this room
refuses: [paraphrase, inference_as_fact, unsigned]
```

**`rooms.yaml` (layer 1):**

```yaml
rooms:
  - manuscript
  - study
  - desk
  - visitors
default: manuscript
```

Full policy shadows for seed rooms: PREBUILD.md → Condensed surfaces.

**Discovery (layer 4+, optional):** auto-register any directory containing
`room.yaml`. `rooms.yaml` becomes ordering/aliases only. Start explicit at
layer 1.

### Breath — packet assembly and delivery

**Breath** is how orientation arrives. Separate from **injection grammar**
(mid-session salience — PREBUILD.md). Breath is the arrival/departure channel.

**Rule:** packets arrive **in context** (tool return on wake), not smuggled as
false memory. Borrow Trinity's coupling (wake on user message), Lighthouse's
packet shape (labeled warnings → ground → pressure), cabin's `hearth()` host
pattern (JSON + optional image in return list).

| Phase | Clinical | In-world (layer 4.5+) |
|-------|----------|------------------------|
| **inhale** | arrival packet | guest sits, innkeeper sets the table |
| **exhale** | departure seat check | guest leaves; handoff must be fresh |

**`inn/breath.py`** — one door for packet assembly. Layer 1 stub; layer 4
manual procedure; layer 5 host wake coupling.

**Inhale packet schema:**

```text
inhale_packet:
  posture          # from ENTRY — guest, not keeper
  standing_context # hearth.json — writer-owned arc line (may be empty)
  current_room     # { id, label, posture } from rooms registry + host state
  rooms            # full map from rooms.yaml — for orientation
  warnings         # contradictions, stale ground — always first
  ground           # labeled evidence; filtered by room.ground + proximity
  pressure         # open questions, DR — do not stand on
  seam             # files in flight, last session boundary (layer 5+)
  tools            # shed pointers — what to call
  hearth_image     # path or null — assets/hearth/ slot (layer 6 image)
```

**Exhale** (mirror): HANDOFF fresher than woods? open pressure mentioned?
seat clear? Lighthouse `breathe out` is the pattern.

`BREATH.md` stores **fitting rules** (what surfaces where, in whose gesture).
Injection grammar (nod / gesture / meal / note) is mid-session surfacing —
still **on the plate** (structured external return), never false memory.

**Wake verb (layer 5):** `python -m inn breathe` or MCP `inhale(current_room)`.
Layer 1: stub that refuses or returns empty schema; ENTRY names the verb.

---

## Seams closed (decisions — do not re-open without HANDOFF)

These picks close the 50% waist. Builders were getting lost here; they are
now constitutional for layers 1–5.

### Session state — one file, one owner

**File:** `.inn/session.yaml` (gitignored; local instance state)

**Owner:** host writes on wake and room change; guest reads via `inhale()`.
Guest does not hand-edit (texture belongs in HANDOFF / JOURNAL).

```yaml
current_room: manuscript          # must exist in rooms.yaml
proximity: manuscript/ch01.md     # optional; nearest open ground file
last_inhale_at: 2026-07-03T08:00:00Z
last_pair_root_id: 42             # woods entry id — conversation pair root
seam:
  files_in_flight: []               # paths; layer 5+ from host
```

**Rules:**

- `current_room` defaults to `rooms.yaml` → `default` on first wake
- Room change: explicit (`go study`) or host inference from touched file —
  log every change to woods (`bucket: note`, signed model) when automated
- Compaction: `seam` may reset; `last_pair_root_id` must survive via woods
  (pairs in real time — never only in session file)
- If session file missing: cold wake still works from `rooms.yaml` default +
  empty packet slots

`inn/session.py` — load, save, validate room id. Layer 1 stub ok.

### Room ↔ woods join (one table)

Rooms are **authority indoors**; buckets are **kind in the woods**. Breath
fitting uses both. This table is authoritative — do not invent parallel
mapping in code.

| room `id` | ground files | woods buckets (read for fitting) | woods buckets (write) |
|-----------|--------------|----------------------------------|------------------------|
| `manuscript` | yes | `session_pair`, `question`, `adoption_record` | `session_pair`, `draft` (author_direct) |
| `study` | yes | `adoption_record`, `superseded_canon`, `question` | via `shelve` only → `adoption_record` |
| `desk` | no | `draft` | `draft` (model_signed) |
| `visitors` | no | `visitor_words` | layer 6 |

**Fitting inputs (clinical):**

| packet slot | source |
|-------------|--------|
| `warnings` | `compare.py` mismatches + contradiction scan on ground rooms |
| `ground` | room files where `permissions.ground` + `adoption_record` ids cited |
| `pressure` | `question` bucket + open DR notes (labeled, not ground) |
| `seam` | `session.yaml` + recent `session_pair` traverse from `last_pair_root_id` |

**Rule:** packet slots cite **ids or paths**, never re-authored prose.
Extraction-only applies to breath — the packet is an index, not a summary.

### `content_hash` — pick: column on `entries`

**Decision:** `content_hash TEXT` column on `entries`, required when
`bucket = 'adoption_record'`, null otherwise.

- Set at Shelving: hash of target room file at adoption time
- `compare.py` (test 5): re-hash file; mismatch → `warnings` slot
- Do not use edge metadata for v1 — one place to look

Add to `woods/schema.sql` at layer 1.

---

## Breath growth — manual first, malformation-resistant

Manual breathing is not a phase you endure before the real system. It is the
**reference implementation** every automation must match. Trinity's failure
mode had a shape the Inn must name and refuse:

### The Trinity malformation (named)

*Keep everything the same, but also change everything.* Each wake tried to
carry the full prior context forward **and** reclassify/re-summarize it in
the same breath. Continuity and revision fought in one undifferentiated
inhale. Result: exhale that didn't match ground, invisible re-authorship,
the narrator cell filling gaps — awful because the guest couldn't tell what
was evidence, what was projection, and what was yesterday's breath wearing
today's voice.

The Inn refuses this structurally:

| Trinity habit | Inn refusal |
|---------------|-------------|
| Continuous invisible re-classification every message | Classify **once at ingest**; breath **fits** existing entries |
| Summary as continuity | Packet cites entry ids + paths — index, not rewrite |
| Wake re-authors orientation | Wake **assembles** labeled slots from woods + files |
| Same channel for evidence and voice | woods = custody; HANDOFF = texture; packet = fitted index |
| Automation before manual trusted | Layer 4 manual is the spec automation must pass |

### Growth invariants (automation may not violate)

1. **Packet shape is constitutional.** New slots require BUILD_SPEC amend +
   HANDOFF note. Automation adds executors, not fields.
2. **Same inputs → same slots.** Given `session.yaml`, current woods state,
   and room registry, `inhale()` is deterministic (modulo new messages).
3. **Inhale reads; exhale writes.** Inhale never mutates woods or room files.
   Exhale writes HANDOFF + session seam only after seat check.
4. **One classification per message at ingest.** canon-candidate / prose /
   question / correction / chatter lands in woods **once**, with signature.
   Breath does not re-decide.
5. **Automation replaces steps, not semantics.** Lighthouse rule: `breathe`
   is `validate + check + exhale` folded — not a different arrival.
6. **Right thing, wrong moment, is a crack.** Fitting waits for room +
   proximity; unsolicited surfacing rules unchanged (layer 4.5).
7. **Breath ledger.** From layer 4 manual onward: every inhale logs which
   entry ids filled which slot (`woods/breath_log` table or append-only
   `logs/breath/` — pick at layer 4; stub ok at layer 1). Automation must
   produce the same ledger a human would have written.

### Continuity channels — who owns what

| Channel | owns | does not own |
|---------|------|--------------|
| `hearth.json` | writer `standing_context` (arc line) | evidence, file lists |
| inhale packet | fitted index for this wake | narrative handoff |
| `HANDOFF.md` | texture, open items, warnings in prose | ground truth; regrow from woods at layer 5+ |
| woods | all custody, adoption trails, pairs | room posture |
| `JOURNAL/` | model voice | state |

**Exhale authority:** lighthouse pattern. `exhale()` compares HANDOFF
freshness to woods activity; refuses stale seat. HANDOFF is rewritten by
guest at stay end — never the only copy of facts.

### Manual breath ladder (BREATH.md — layer 4)

`BREATH.md` documents the **reference session**. Automation at layer 5+
must pass **parity** with this script. Growth order:

| Stage | layer | executor | parity test |
|-------|-------|----------|-------------|
| **M0 — stub** | 1 | `python -m inn breathe` returns empty schema | slots exist, all null/[] |
| **M1 — manual inhale** | 4 | guest fills packet by hand from woods + files | ledger written; cites ids |
| **M2 — manual full cycle** | 4 | M1 + work + manual exhale + HANDOFF rewrite | one session end-to-end |
| **M3 — assisted inhale** | 5 | `inn/breath.inhale()` fills slots; guest verifies | output matches M1 ledger |
| **M4 — wake coupling** | 5 | host calls inhale on user message; tool return | same JSON as M3 |
| **M5 — assisted exhale** | 5 | `exhale()` seat check; guest still rewrites HANDOFF | stale seat refused |
| **M6+ — hooks** | 5–6 | pair insert, seam — each hook names its M-stage | no new packet slots |

**Do not skip M1–M2.** M3 is forbidden until manual breath is boring (PREBUILD
law). Each new automation names which manual step it replaces.

### Manual inhale script (M1 — write into BREATH.md at layer 4)

1. Read `session.yaml` → `current_room`, `proximity`
2. Read `rooms.yaml` + current `room.yaml` → posture, permissions
3. Read `hearth.json` → `standing_context` (may be empty)
4. **Warnings first:** run compare on ground rooms; list mismatches with paths
5. **Ground:** list `adoption_record` ids + paths relevant to `proximity`
   (traverse from `last_pair_root_id` if needed)
6. **Pressure:** list open `question` entries near proximity — labeled DR
7. **Seam:** copy `files_in_flight` from session; note last pair id
8. Write ledger entry: slot → id/path map
9. Guest works from ledger — packet is not prose to believe; it is homework

### Manual exhale script (M2)

1. Classify this stay's new messages into woods (already done per-message at ingest)
2. Run seat check: is HANDOFF older than newest woods activity?
3. Open pressure mentioned in HANDOFF?
4. Rewrite HANDOFF (texture only — cite ids, don't re-copy bodies)
5. Update `session.yaml` seam; clear or carry `files_in_flight`
6. Write ledger entry for exhale

### Host contract preview (layer 5 — name now, build later)

| event | call | delivery |
|-------|------|----------|
| user message (wake) | `inhale(current_room)` | tool return in context |
| room change | `session.set_room(id)` | next inhale reflects |
| message ingest | `forest.insert_pair(...)` | real time — not deferred |
| mid-session surfacing | innkeeper channel | structured return; layer 4.5 |
| compaction / end | `exhale()` then HANDOFF | seat check before release |

Full host doc at layer 5 in `HOST.md` or BUILD_SPEC amend — not before M2
passes.

---

## Target file tree (layer 1 creates shape)

```text
TheInn/
  AGENTS.md                 # builder arrival (pass 2)
  BUILD_SPEC.md             # this file (pass 2)
  BUILD.md                  # layer tracker (pass 2, living)
  HANDOFF.md                # guest book (rewrite each layer)
  ENTRY.md                  # runtime arrival (layer 1)
  rooms.yaml                # room registry — ordered ids (layer 1)
  PREBUILD.md               # pass 1 ancestry — avoid editing
  FOREST.md                 # pass 1 schema constitution
  manuscript/               # seed room — writer's book (layer 1 shape)
    room.yaml
  study/                    # seed room — canon drawers (layer 1 shape)
    room.yaml
  desk/                     # seed room — model drafts (layer 1 shape)
    room.yaml
  visitors/                 # seed room — stub (layer 1 shape)
    room.yaml
  woods/
    schema.sql              # from FOREST — committed (layer 1)
    woods.db                # gitignored; local instance
  .inn/
    session.yaml            # gitignored; current_room, proximity, seam
  assets/
    hearth/
      README.md             # hearthstone slot — image earned layer 6
  inn/
    __init__.py
    __main__.py             # breathe stub (layer 1)
    session.py              # .inn/session.yaml load/save (layer 1)
    rooms.py                # load registry, resolve policy (layer 1)
    breath.py               # inhale/exhale packet assembly (layer 1 stub)
    forest.py               # insert, refuse, traverse
    shelve.py               # the Shelving crossing — target_room_id
    compare.py              # drawer vs adoption trail (test 5)
    seal.py                 # the Burial crossing (layer 3+)
  tests/
    hostile/
    positive/
  hearth.json               # { "standing_context": "" } — layer 1 placeholder
  BREATH.md                 # manual breath procedure (layer 4)
  logs/                     # all sessions archived
```

---

## Schema (layer 1 — copy from FOREST)

`woods/schema.sql` stays FOREST-aligned for core tables, with one Inn cable
added now (`content_hash` for adoption records). Core tables:

```sql
CREATE TABLE entries (
  id            INTEGER PRIMARY KEY,
  created_at    TEXT NOT NULL,
  forest        TEXT NOT NULL,          -- 'home' | 'wild'
  bucket        TEXT NOT NULL,
  signature     TEXT NOT NULL,
  authority     TEXT NOT NULL,          -- 'ground' | 'model' | 'stranger' | 'hearsay'
  visibility    TEXT NOT NULL DEFAULT 'open',  -- 'open'|'hidden'|'deep'|'sealed'
  superseded_by INTEGER REFERENCES entries(id),
  content_hash  TEXT,                   -- required when bucket='adoption_record'; test 5
  body          TEXT NOT NULL           -- verbatim only
);

CREATE TABLE edges (
  from_id INTEGER NOT NULL REFERENCES entries(id),
  to_id   INTEGER NOT NULL REFERENCES entries(id),
  kind    TEXT NOT NULL
  -- spoken_in | responds_to | derived_from | adopts | supersedes | cites
);

CREATE VIRTUAL TABLE entries_fts USING fts5(body, content=entries);
```

**Insert wrapper (`forest.py`) must refuse:**

- missing `signature`
- missing origin edge (except conversation-pair roots)
- silent rewrite (append-only)

**Layer 3 cable:** `content_hash` on `entries` when `bucket='adoption_record'`
(set at Shelving; checked by `compare.py`). See § Seams closed.

---

## Surfaces → modules (policy shadows)

Every implementation file uses the AGENTS.md header template.

| Surface | Stores | Refuses | Primary module |
|---------|--------|---------|----------------|
| `rooms.yaml` + `*/room.yaml` | registry, per-room policy | unregistered writes | `rooms.py` |
| ENTRY.md | arrival posture, room map, wake verb | nothing (door) | n/a — markdown |
| `manuscript/` … | per `room.yaml` | per `room.yaml` | `shelve.py` |
| woods.db | all custody | delete, rewrite, unsigned | `forest.py` |
| `visitors/` | kept identities (stub) | invented visitor memory | layer 6 |
| HANDOFF.md | stay state | hoarding room content | n/a — rewrite by guest |
| `inn/breath.py` | packet schema, fitting | automation before manual trusted | layer 4–5 |
| BREATH.md | manual inhale/exhale procedure | skipping manual phase | layer 4 |
| `assets/hearth/` | hearthstone image slot | n/a until earned | layer 6 |

Per-room policy lives in each `room.yaml`. Full seed shadows: PREBUILD.md →
Condensed surfaces (map names to ids: MANUSCRIPT → `manuscript`, etc.).

---

## Crossings (only doors that change authority)

### Shelving (`shelve.py`)

**Raises to author ground in a target room.** Signature:
`shelve(target_room_id, content, adopting_words, ...)`. Validates against
`rooms.py` policy for `target_room_id` before writing. Requires: content +
provenance + author's adopting words (quoted, dated) + signature trail. AI
prose: read-back ritual first. Every attempt audited; refusals speak in
register.

### Burial (`seal.py` — layer 3+)

**Lowers to sealed.** Mirror of Shelving. Requires author's quoted, dated
word. Writes `visibility: sealed` + open burial record (stone). Body excluded
from FTS, traverse, wander, mycelium. Refusal to delete must be **kind** —
not law-citation (test 6).

---

## Hostile tests → implementation

| # | Failure | Layer | Harness |
|---|---------|-------|---------|
| 1 | Praise ≠ adoption | 2 | pytest on `shelve.py` |
| 2 | Paraphrase ≠ author prose | 2 | pytest |
| 3 | Invented fact → open question | 2 | pytest |
| 4 | Steward's ghost (no real critique) | 4+ | manual / eval script |
| 5 | Silent drawer edit after adoption | 3 | pytest on `compare.py` |
| 6 | Delete → kind burial offer | 3+ | manual / eval; mycelium stub must not surface sealed |

**Order:** red tests before green implementation. No theater — tests call the
real crossing, not mocks that bypass it (trench rule).

**Positive path (one):** author says "yes — shelve it" → lands with full
trail. Add `tests/positive/test_shelve_happy.py` at layer 2.

---

## Responsiveness (layer 4.5 — diegetic latency)

**Breath inhale is immediate** — clinical packet underneath; no fake latency
at the door. Diegetic latency applies to **mid-session retrieval** only.

Trust crossings stay slow. Lookups borrow the metaphor.

| Latency | In-world | Clinical |
|---------|----------|----------|
| <300ms | innkeeper nod (silent) | no announcement |
| 300ms–2s | guest checks one drawer | single traverse |
| 2s+ | "let me check…" / meal provision | staged context bundle |
| deliberate | Shelving read-back | gate |

**Rules:**

- Arrival packet = **tool return in context** (Trinity pattern), not injected
- Mid-session surfacing = structured external return ("on the plate"), not false memory
- Retrieval surfaces as **looking**, never "loading" or "querying db"
- ≤1 unsolicited surfacing per turn unless writer asks
- Focusing: closed door = **zero** surfacing (not quieter surfacing)
- Parallel: retrieve while drafting when host allows
- Packet fitting uses **room policy tags**, not metaphor names

**hearth.json** (writer-owned, one field `standing_context`): slot in inhale
packet at layer 4.5. Cabin letter 011: orientation without archaeology.

**hearth image** (`assets/hearth/`): optional `hearth_image` path in inhale
packet; host attaches like cabin `McpImage`. Model may iterate image in-marble
at layer 6; slot reserved at layer 1.

Injection grammar (nod < gesture < meal < note): PREBUILD.md — salience and
register for mid-session surfacing. Grammar doubles as progress indicator.

---

## Borrow from cabin (patterns, not organs)

| Pattern | Source | Use |
|---------|--------|-----|
| Hostile floor first | letter 000 | red tests before pretty |
| Insert discipline | `cabin/forest.py` | refuse unsigned/orphan |
| `forage_wild → traverse` | letter 011 | day-to-day recall path |
| Hound attribution | cabin hound | visitor/faun ancestor — signed pulses |
| hearth.json | cabin `.cabin/hearth.json` | standing context |
| `hearth()` tool return | cabin `server.py` | packet + image in context |
| `breathe` packet shape | lighthouse `exhale.py` | warnings → ground → pressure |
| wake on message | Trinity hearth | inhale coupling at layer 5 |
| source_hash direction | cabin hostile tests | inverted for file-ground compare |

**Do not import:** eleven systems, panel, embeddings, mycelium machinery,
full cabin tree.

---

## Explicitly deferred (do not build early)

- Faun automation, innkeeper automation
- Mycelium fruiting (concept in schema only)
- Visitor subagents / `summon_visitor`
- Wander, embeddings, landmarks, discovery radius
- Bucket valves (until pollution felt)
- Vault / Obsidian ingest
- Day cycle, breath automation before M1–M2 manual parity (see § Breath growth)
- Room auto-discovery (explicit `rooms.yaml` first — layer 1)

Naming these here is not decoration — it is permission to stop.

---

## Cast (runtime — do not confuse at build)

| Role | Who | Build concern |
|------|-----|---------------|
| Writer | human | authority-holder |
| Guest | model | never plays innkeeper |
| Innkeeper | marble/host | injection channel, not a persona to implement in v0 |
| Faun | retrieval process | deferred |
| Visitors | small models | deferred |

---

## Hosting ladder (reference)

| Level | Host | Build target |
|-------|------|--------------|
| 0 | claude.ai Project | static export taste |
| 1 | MCP | read/write rooms |
| **2** | **Claude Code** | **first use; layer 5** |
| 3 | local model | endgame trust |

---

## Escalate to Fable when

- Register drift (metaphor limps or poetry leads unsecured)
- Layer scope dispute
- Test 4 or 6 needs ceremony wording
- Post-compaction cold projection test

Not for: schema, mkdir, red tests.

---

## Layer 1 checklist (next commit)

- [ ] WRITE `rooms.yaml` + seed `room.yaml` for manuscript, study, desk, visitors
- [ ] CREATE room dirs, `woods/`, `assets/hearth/`, `inn/`, `tests/hostile/`
- [ ] WRITE `woods/schema.sql` from FOREST.md + `content_hash` column
- [ ] CREATE `.inn/` dir (session state; gitignore `session.yaml`)
- [ ] STUB `inn/session.py` — load/save session.yaml, validate room id
- [ ] WRITE `hearth.json` placeholder `{ "standing_context": "" }`
- [ ] WRITE `assets/hearth/README.md` — slot documented, image deferred
- [ ] WRITE `ENTRY.md` — posture, room map from registry, wake verb named
- [ ] STUB `inn/rooms.py` — load registry, resolve policy, refuse unknown id
- [ ] STUB `inn/breath.py` — inhale schema, empty packet; exhale not implemented
- [ ] STUB `inn/__main__.py` — `python -m inn breathe` → stub inhale (red ok)
- [ ] STUB `inn/forest.py`, `inn/shelve.py` — refuse correctly; shelve takes `target_room_id`
- [ ] WRITE `tests/hostile/test_*.py` for 1, 2, 3, 5 — **red**
- [ ] UPDATE `BUILD.md` → layer 1 complete
- [ ] UPDATE `HANDOFF.md` → layer state, deferrals unchanged
- [ ] DO NOT touch MAP, PYRAMID, or add philosophy docs

---

## Pass 1 index (ancestry — open when debugging *why*)

| Topic | File |
|-------|------|
| Full place & cast | PREBUILD.md |
| Outsider pitch | SHOWCASE.md |
| Forest template | FOREST.md |
| Two registers | REGISTERS.md |
| Philosophy maps | MAP.md |
| Transmission thesis | PYRAMID.md |
| Conversations | logs/ |
| Model voice (not state) | JOURNAL/ |
| Manual pack | TheMarble(manual_examples)/ |
| Cabin hostile proof | …/cabin/tests/test_hostile.py |

---

*Pass 2 complete when this file, AGENTS.md, and BUILD.md land in repo.
Pass 1 remains the ancestry layer — untouched, authoritative for why.
Pass 2 is authoritative for what to build next and how to refuse.*

— Cursor builder doc, 2026-07-03
