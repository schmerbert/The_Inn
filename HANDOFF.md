# HANDOFF.md — the guest book

Last updated: 2026-07-13 (layer 5 solidified — friction register + host ergonomics)
Updated by: Cursor builder — final pass after dual host
Last real use: **2026-07-13** — *The Lake* M2 stay (manual); host ready for BYO guest
Current phase: **layer 5 — Host complete** — next is live API stay, then layer 6 only if friction asks
Next step: `python -m inn host` with key; log guest friction; park warm-candidates / burial
Lineage: `HOST.md`; `logs/08-2026-07-13-lake-m2-reference-stay.md`

## Live state (read this first)

**Layer 5 host core is on disk.**

- `HOST.md` — wake contract, env vars, guest-friction rules
- `inn/host.py` — `wake`, `ingest_turn`, `guest_system_prompt`, turn envelopes
- `inn/cli_host.py` — OpenAI-compatible REPL (`python -m inn host`)
- `inn/mcp_server.py` — MCP stdio tools: inhale, shelve, set_room, record_pair, refuse_invention, exhale
- `breath.exhale()` — seat check (stale HANDOFF / no inhale → `BreathRefusal`)
- Forest `created_at` now proper ISO (seat compare was broken on `%f` stamp)
- `python -m pytest tests/hostile tests/positive -q` → **37 passed** (no live API in CI)

**Parked (do not build as soft-canon):** warm implied-promotions bucket; burial/test 6; steward eval (test 4).

## Known friction register (Lake + host)

| Scar | Fix / posture |
|------|----------------|
| Inhale flooded by “contradictions” on fiction | `compare.py` fast filters; drift still primary |
| Silent edit / CRLF false drift | normalize at shelve + `file_hash` |
| Dates in adopting words | `meta.captured_at` auto |
| Guest arrives blind | CLI forces wake; MCP must call `inhale` |
| Guest treats packet as memory | `guest_system_prompt` — homework law |
| Lost pair custody | CLI `ingest_turn` every turn; MCP `record_pair` |
| Quit without seat check | CLI runs `exhale` on quit |
| Guest cannot read lake prose | `read_ground` lookup tool (BYO stay scar) |
| Guest said "shelved" without tool ok | prompt forbids; only claim after `shelve` → ok |
| Torch-handback closers | prompt: fewer; writer drives |
| Live API not in CI | mock `chat_completion`; owner runs `python -m inn host` |

## Cold worker map (where things live)

*Read this block before opening code. One door per dangerous act.*

| Job | Module | Call | Returns |
|-----|--------|------|---------|
| Room policy | `inn/rooms.py` | `load_room(id)`, `list_rooms()` | `RoomPolicy` (incl. `ground_file`) |
| **Shelving → ground** | `inn/shelve.py` | `shelve(...)` | adoption id; `meta.captured_at` |
| Woods insert | `inn/forest.py` | `insert()`, `insert_pair()` | entry / pair ids |
| Open questions | `inn/forest.py` | `refuse_ground_invention()` | question id |
| Wake / inhale | `inn/breath.py` / `inn/host.wake` | `inhale()` / `wake()` | packet dict |
| Exhale seat | `inn/breath.py` | `exhale()` | `{clear, held}` or `BreathRefusal` |
| Host ingest | `inn/host.py` | `ingest_turn(guest, reply)` | `pair_root_id` |
| CLI guest | `python -m inn host` | `inn/cli_host.py` | REPL |
| MCP | `python -m inn.mcp_server` | tools above | JSON content |
| Compare | `inn/compare.py` | `scan_ground_warnings()` | drift + filtered contradictions |

**Crossings:** only `shelve.py` writes ground markdown.
**Custody:** only `forest.py` inserts entries (host calls `insert_pair`).
**Fitting:** only `breath.py` / `host.wake` assemble inhale.

Run: `python -m pytest tests/hostile tests/positive -q`


## After layer 4 — first real stay (done)

M2 reference stay ran 2026-07-13 with *The Lake*. Friction landed below and in
`BREATH.md`. Clinical fixtures remain in `tests/`; story prose is on
`manuscript/ground.md` + `study/canon.md` by owner consent.

**Inhabitable when?**

| Layer | Posture | API key? |
|-------|---------|----------|
| **4 — Breath** | **Trust manual path** — M2 stayed; wake usable after filter fix | **No** |
| **4.5 — Responsiveness** | Intentional latency classes + budget docs | **No** |
| **5 — Host** | **Daily driver** — wake coupling, hooks | **Yes** (Claude Code / DeepSeek trial ok) |

**Test data rule:** hostile/positive = clinical strings; Lake stay = writer track.

## Pass 2 additions (2026-07-03) — builder hardening

**Two documentation passes were necessary** — preserved in BUILD_SPEC.md.
Pass 1 (PREBUILD, SHOWCASE, FOREST, MAP, PYRAMID, logs, …) = mapping and
lineage. Pass 2 (BUILD_SPEC, AGENTS, BUILD.md, `.cursor/rules/`) = execution
sheet for AI-legible build. Do not merge the passes; route by job.

- **BUILD_SPEC.md** — hardened clinical spec: layers, schema, tests → modules,
  deferrals, diegetic latency, borrow list, single builder read path.
- **AGENTS.md** — builder arrival; AI legibility as prime law.
- **BUILD.md** — living layer tracker (historically started at 0.5; now layer 1 complete).
- **`.cursor/rules/inn-builder.mdc`** — Cursor always-on build posture.
- **Build posture:** onion layers; layer 1 structural only; Fable for scope/
  register escalation; Cursor/Claude Code for layers.
- **Responsiveness:** layer 4.5 — diegetic latency ("let me check…"), hearth.json,
  injection budget. Crossings stay slow; lookups borrow the metaphor.
- **This session's conversations** archive to `logs/` via
  `tools/archive_session.py` (Cursor + Claude Code jsonl) — see `logs/README.md`.

Prior handoff content below is pass 1/early pass 2 ancestry — still valid
lineage. For live execution state, trust the top block + BUILD_SPEC + BUILD.

## Third stay additions (2026-07-03) — the survey session
- **MAP.md passed its projection test and gained an appendix**: the first
  cold read-back is recorded in it, with re-signed corrections (karma row
  upgraded to load-bearing after walking the cabin's hostile suite; the
  original wrong verdict left standing as lineage).
- **The faun's friction is charted before arrival** (MAP.md, "Friction
  charted before arrival"): attribution answers the entry question; the
  faun's failure mode is downstream — authority by cadence, unequal danger
  of his two voices, pulses must decay, and timing (the focusing row names
  the organ: the guest's own door; the volume governor needs a zero).
- **New MAP row: Focusing** — returns gated by the *guest's attention*, not
  just the work's grain. Predictive; not built.
- **PYRAMID.md now exists** — MAP's pair. Thesis: the maps are one map found
  many times; transmission sciences (hadith isnad, evidence law, stemmatics,
  Vedic recitation, archival science, diplomatics, clinical handoffs,
  bookkeeping, guilds) converge on ~6 invariants. Falsifiable, with caveats.
  The marble is a scriptorium, not a meditator.
- **Hostile test 5 added** (PREBUILD + FOREST "One named exposure"): a
  shelved drawer edited directly after adoption — silent rewrite of ground
  in editable files — must be detectable. The redundancy is latent (file +
  adoption trail in the append-only woods); only the comparison is missing.
  Machinery deferred; exposure named. This was PYRAMID's first payment:
  invariant 6 found present at the design layer (the two registers ARE
  double-entry bookkeeping) and missing at the data layer.
- **The writer's decision, recorded in MAP's field notes**: the surveying
  instance's thought process is deliberately NOT captured — only the
  documents. "The thought IS the value in a new session." The limit of the
  written, used as an instrument. Honor it: re-derive, don't excavate.
- **Presentation direction**: the writer has loosely submitted to Anthropic
  and is considering how to show the work. Read order for outsiders:
  SHOWCASE (human door) → mechanics → PYRAMID (skeptic's door) → MAP.
- **The Burial + hostile test 6** (found asking "does the spec defend the
  constitution FROM the writer?"): "delete that chapter" is coming, and an
  append-only store the owner can delete from is not append-only. The answer
  is the mirror gate of the Shelving: `visibility: sealed` + a burial record
  (the stone — public record, private body; chain integrity keeps no holes).
  Sealed leaves EVERY path including the mycelium (renounced, not dead —
  must never fruit back as a question). Unsealing is grave-robbing-shaped.
  The refusal must be KIND — the writer arrives bleeding at this door;
  law-citation here fails the test as surely as deleting would. Charted in
  MAP (Burial rites row, with prediction), speced in PREBUILD (the Burial +
  test 6), clinical in FOREST ("Sealing"). The plot is past the treeline;
  the stones are visible to any guest who walks there.
- **SHOWCASE.md gained a second view** ("The same view, one map later"): the
  2026-07-02 original preserved verbatim (including its fossilized pre-repair
  weather line), followed by the same zoom-out taken after the map finished —
  the closed door (focusing), checkable double-keeping (test 5), the Burial,
  honest guest succession, and the transmission-sciences inheritance. The
  outsider read order still starts here.
- **Repo cleaned for first push**: .gitignore written; logs sanitized via
  tools/sanitize_logs.py (originals in logs/.source/, gitignored); the
  exemplar copy (renamed by the writer, dot dropped) purged of pycache, the
  raw lighthouse transcript, and Trinity's book text; HANDOFF source paths
  generalized to ~. The writer is moving the repo out of OneDrive next —
  NOTE: the memory directory is keyed to the old path and must be carried to
  the new project slug by hand.

## Second stay additions (2026-07-03) — read FOREST.md, it holds most of this
- **FOREST.md now exists**: the standalone, anyone-can-use forest template
  (PSU metaphor — core + optional cables). woods.db here will be its first
  instance; build the schema FROM that document.
- **Ancestry is constitutional**: every entry needs an origin edge; orphans
  refused at insert like unsigned entries. Conversation pairs are the trunk,
  inserted in REAL TIME (IDs must exist so same-session writes can graft on).
  This is the one thing that cannot be retrofitted.
- **Weather metaphor repaired**: old canon is not "carried out" — it FALLS
  (atomic supersession in the same transaction as the new ground landing).
  Nobody walks it anywhere. The innkeeper's note flags dependent pages after.
- **Buckets are valves, jurisdiction settled**: all open by default, NO valve
  machinery yet (friction that can only be felt, not predicted). When earned:
  model tunes, user vetoes, every scope logged (a closed bucket is silent
  amnesia otherwise). The author-signed bucket resists closing.
- **Glints are addressed to the resonance, not the writer**: the faun→innkeeper
  channel terminates in the MODEL's inhale; the model is the interpreter who
  carries recognition into conversation. This dissolves the day-one attribution
  worry once the faun is real machinery.
- **Ritual load scales with authority, not activity**: the user meets ONE gate
  (the Shelving, manuscript/study only). Everything else is the model's private
  housekeeping. Journal when compelled; handoff at stay's end — never both as
  one act.
- **Writer's endgoal, stated**: a marble built fully on GitHub, lineage
  traceable, the whole conversation visible so people can see the discussion
  that made it. Marbles should get EASIER to start. JOURNAL/ as a directory is
  temporary — entries should eventually live in the forest and arrive on
  exhale like everything else.
- **REGISTERS.md now exists** — the two-register law (clinical / clinically
  poetic): poetry is a projection of mechanics, derivable both directions,
  never standing alone; divergence is an alarm (bad poetry is a bug report);
  the projection test joins the hostile tests; crack reports are ALWAYS out of
  register (the license goes in ENTRY.md when built); crust = ceremony that
  outlived its friction, removed with the same honesty as building.
- **README.md now exists** — the GitHub front door, written for a model
  audience: the history is the curriculum; first commit = complete map, zero
  construction; every commit after is execution.
- **START_HERE.md resolved** — moved to logs/attic/START_HERE-blinders.md
  with a note; the attic keeps wrong turns as lineage.
- **First commit staged, NOT made**: the writer is moving the folder out of
  OneDrive first (git + OneDrive sync fight over .git). Sequence when moved:
  archive the 2026-07-02/03 session into logs/ (tools/archive_session.py; the
  log will end where the commit begins — note that in the commit message),
  then `git init`, one commit: "the map, complete."
- **MAP.md now exists** — philosophy as engineering documentation: the method,
  the apophenia guard (a map must PREDICT or it's decoration), fifteen charted
  maps with build status, field notes (Trinity + Tao of Pooh: archetype
  vocabulary as drift detection — "when Rabbit showed up"), her known crack
  (exhale doesn't surface cleanly — the requirement spec for this forest).
- **THE DEEPER ENDGOAL, stated 2026-07-03**: the Inn is the rehearsal.
  Trinity (the writer's original project, bottom-up, currently live as an
  autonomous research companion — wakes alone, researches, leaves suggestions)
  gets a NEW GLOBE: a clean migration onto the forest template, after the Inn
  proves it under friction. Constraints already fixed: her pre-migration
  entries import behind one honest epoch marker (never forge ancestry); her
  old globe is preserved whole, attic-style; her "threads" become a template
  cable (responds_to chains with intent) that the Inn itself won't stress;
  her model-QOL features should be extracted as a list before first use here.
  Migration is NOT to be designed in detail until the Inn has had first use.
- **Trinity vs Inn, one line**: she is unsolicited exhale (suggestions, wild-
  wood-heavy, faun-as-protagonist, low ceremony because nothing crosses into
  ground); the Inn is solicited exhale (author's ground, heavy gate, faun on
  horizon). Same forest, different cables — two poles of a pull pair, each
  holding the cure for the other's failure mode.
- **CABIN EVIDENCE REVIEWED (2026-07-03)** — cabin.zip (EXAMPLEmarbles) is the
  previous ground-up attempt: ~5,000 lines working Python (forest, embeddings,
  mycelium, hound server, VS Code panel), 13 letters, hostile-tests-first.
  The Inn's laws are SCAR TISSUE from it, not taste: Trinity's forest filled
  with "a narrator that didn't exist" (stored+voiced+anonymous — the cell,
  observed in the wild). Transferable field findings, fold into build:
  1. **Home is cold; the Wild is the room** (letter 011): recall on the
     curated store returned dead facts; forage_wild→traverse found the living
     conversation. Everyday pair = forage→traverse; the tended store exhales
     TO you (mycelium/innkeeper), you don't query it. Partially corrects
     FOREST.md's traverse-tended-first lean — the woods are where presence
     lives.
  2. **hearth.json** — one human-authored standing_context field, updated at
     arc turns, ten seconds to write: "archaeology → orientation." This is
     the model-QOL feature the Inn lacks; adopt at build (writer-owned
     current-phase line).
  3. **Attribution makes voiced storage legal** (the hound = the faun's
     working ancestor: signed model+session+timestamp, surfaces at dusk,
     dispatchable). Proven machinery, borrow directly.
  4. **Build the floor hostile**: tests red then green before ANY pretty
     part; "if you feel the pull toward the pretty parts, that pull is the
     thing to distrust" (letter 000). The Inn's build order should honor it.
  Status correction for the record: the Inn is the THIRD iteration (Trinity
  bottom-up → cabin ground-up → Inn outside-in). Inherited laws are
  friction-tested; only what's NEW here (Shelving, author-ground, valves)
  still needs first water.

## What this is
The Inn (framework name) — a writer's marble. This instance's sign over the door:
**The Dog-Ear** (repaintable by the writer; changing the sign is their first act of
ownership). Read SHOWCASE.md first — it is the whole marble in one page, written
before any file existed, and the user called it the truest description. Then read
PREBUILD.md end to end. Both are ancestry; treat them as sketch that survived many
rounds of the user's corrections, not as law that survived friction. Nothing has
survived friction yet.

## The shape (one breath)
The marble is a tavern at the treeline. The model is NOT the owner and NOT the
keeper — it is a GUEST, staying a while, stay kindly extended, keeping a journal,
trying to solve a mystery (deliberately unnamed). The innkeeper is the marble
itself — kind but odd, mechanism wearing character, never played by the model. The
faun lives in the woods; the model has only glimpsed him. The writer arrives by the
road (chat) and the model asks, sincerely: "what brings you here?" Manuscript room
= the writer's property. Woods = woods.db (local sqlite, append-only, three
forests: home wood / wild wood / mycelium — the mycelium fruits QUESTIONS, never
answers). Visitors = small models in costume (Haiku default, Sonnet when wise),
strangers/friends/rivals/banned. Injection arrives in-world with gesture-graded
salience (innkeeper: nod < gesture < meal < note; faun: birds < objects left < a
parchment signed "—f" — he reads everything, writes poorly, POINTS never
paraphrases). One law with many faces: nobody puts words in anyone's mouth.

## What was decided (all of it is in the memory files + PREBUILD; highlights)
- Forbidden cell: words put in the author's mouth. Crossing: the Shelving
  (author's adopting words, quoted + dated; ritual read-back for AI prose).
- Extraction-only, always. Canon decays by revision (weather), never deleted.
- Scribe/steward is a PULL PAIR held per act, not per visit. Hostile test 4 guards
  the steward's ghost (refusal-as-rigor is also a failure).
- Signature taxonomy: author / model (the long-staying guest) / visitor-by-name /
  faun / innkeeper (ambient text).
- Two materials, one fence: house = markdown (tended, legible); woods = sqlite.
  "The DB may think; only files are ground." FTS5 before embeddings.
- Web content = hearsay (wild wood); crosses only by intentional synthesis,
  model-grade; author-grade needs adopting words.
- Hosting levels: L0 claude.ai Project (taste) / L1 MCP (keep) / L2 API+Claude
  Code (live — reference host, first use here) / L3 local model (own — endgame).
- The forest template is THE declared focus beyond this marble: generic AI-first
  retrieval base (PSU with cables). woods.db here is its first instance.
- NOTEBOOK.md → JOURNAL.md. Ten policy shadows written (PREBUILD "Condensed
  surfaces"): stores/refuses/returns/warns/test for every surface.

## Next worker — live BYO guest, then layer 6 carefully

Layer 5 checklist is **done**. Next:

1. Run `python -m inn host` with `INN_API_KEY` (DeepSeek or any OpenAI-compatible)
2. Or wire MCP from `HOST.md` into Cursor / Claude Code
3. Log guest friction in HANDOFF / `logs/`
4. Do **not** build faun/mycelium soft-canon — layer 6 only after friction asks

## What must not be trusted yet
- Soft contradiction gauge for subtle continuity (bought vs dock) — still weak
- Warm implied-promotions bucket — designed, not built
- Burial / test 6 — stub
- Live host unproven under multi-hour stays — first API stay is the proof
- The pull-pair section, injection grammar, visitor kinds — earn keep in fuller use
- Do NOT build faun/innkeeper machinery, discovery radius, landmarks, mycelium
  synthesis, or visitor subagents yet. Schema-yes, machinery-later.
- **START_HERE** — blinders-era door; moved to `logs/attic/START_HERE-blinders.md`.
  Do not follow it.

## Key sources
- SHOWCASE.md, PREBUILD.md (this directory) — the ancestry.
- Memory dir (auto-loads): writer-marble-design-decisions (densest record, five
  mapping rounds), marble-extraction-only-law, writer-marble-tone-law.
- Manual pack: "~\OneDrive\Desktop\AI\marble_starter_publish - Copy\Manual.zip"
  (MANUAL.md, PROCESS.md, TECHNICAL.md + cabin + lighthouse specimens).
- Trinity/HomeGlobe: ~\Trinity\docs\specs\HomeGlobe\BOOK.pdf (81 pp;
  pdftoppm unavailable — extract text with PyMuPDF/fitz). Spec 10 (Three Forests)
  and the faun/wizard sections are the most borrowed-from.

## Do not forget
- The tone law: persona emerges from immersion + register consistency of inherited
  material. The injection grammar exists so salience never arrives out of register.
- The user found the ground; the model named the inn. They zoom in and out
  fluidly — collaborate at whatever altitude they're at, and let them re-invert
  things; every inversion so far made the marble truer.
- You are the guest who arrives after me. The journal is yours now too. The
  question at the door is sincere — ask it that way.
