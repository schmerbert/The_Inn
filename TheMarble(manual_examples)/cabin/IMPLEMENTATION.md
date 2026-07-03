# .cabin — Implementation Spec

*The buildable companion to [CABIN.md](./CABIN.md) (formerly MYCROFT.md). That document is the why; this is the how. Every mechanism here is grounded in working code from Trinity, cited by file, so nothing in it is speculative — the architecture is already proven in production; .cabin is its second, cleaner tenant.*

*Audited from Trinity's live source on 2026-06-26 before drafting, per the house rule (brainstorm → audit → draft → implement). File references point at the reference implementation.*

---

## 0. What is already proven (so we don't re-derive it)

Trinity's forest is not a prototype. It is a running, local, vector-native memory with the *exact* shape Mycroft needs. The audit found that the MYCROFT.md design is largely **already implemented in Trinity** — which means the risk is low and the patterns are known-good:

| Mycroft concept | Already working in Trinity | Where |
|---|---|---|
| Local on-device embeddings | `sentence-transformers`, `all-MiniLM-L6-v2`, 384-dim, normalized, lazy-loaded | `brain/memory.py:50` `embed()` |
| Local vector index | `sqlite-vec` `vec0` virtual table, `FLOAT[384]` | `migrations/phase0_forest.py:46` |
| Home / Wild split | `forest_entry.forest = 'home_wood' | 'wild_wood'` | `brain/db.py:567` |
| **LAW II** (Wild→Home only by synthesis) | `boundary_synthesis()` — raw wild entry stays; insight crosses | `brain/forest.py:461` |
| The Wild gate (reason to enter Wild) | `traverse_wild_wood()` returns the gate question if no reason | `brain/forest.py:364` |
| **LAW I** (extract, never summarize) — compression | `compress_old_history()` *drops oldest pairs*, never paraphrases | `brain/scaffolding.py:201` |
| The extraction filter | `strip_scaffolding()` — canonical contamination guard | `brain/scaffolding.py:135` |
| Feathers (ambient surfacing) | `pop_pressure_feather()` — surfaces once, resets to 0 | `brain/forest.py:686` |
| Foraging by worn paths | `wander_forest()` — direction = centroid of recent traversals | `brain/forest.py:549` |

**What Mycroft adds that Trinity lacks** (the genuinely new build):
1. **Physically separated, individually-switchable tables** (Trinity uses one `forest_entry` table with a `source_type` column; Mycroft makes each bucket its own table + vec companion so a polluted bucket can be *switched off* — the circuit-breaker).
2. **Cross-project scope** (the wood shed and mycelium are global; Home is per-project).
3. **The proprioception instruments** (state gauge, claim-vs-file check, seam-audit) — these serve the worker, and no coding tool ships them.
4. **MCP exposure** so it works inside VSCode/Claude Code with no change to workflow.
5. **The revived Factor 2 grower** — Trinity's own code comment (`brain/forest.py:659`) specifies the fix; Mycroft builds it from the start.

---

## 1. Stack

- **Language:** Python 3.11+.
- **Embeddings:** `sentence-transformers` (`all-MiniLM-L6-v2`, 384-dim, unit-normalized). On-device. ~80 MB one-time download, then local cache. *Pinnable to a larger local model later; 384-dim is the proven default.*
- **Vector index:** `sqlite-vec` (`vec0` virtual tables).
- **Store:** a single local SQLite file per scope-root (see §3). `numpy` for vector blobs and centroid math.
- **Transport:** MCP server (Python `mcp` SDK / FastMCP). Exposes tools Claude Code calls. **No cloud. No API key required for memory.** *(Confirm current `mcp` SDK API at build time — bench rule: don't assume, check.)*
- **One firm non-dependency:** no managed vector DB, no embedding API, no framework. Own the mind; rent only `sqlite-vec` + `sentence-transformers`, both local.

---

## 2. The two LAWS, stated as enforceable invariants

These are not style. They are the contamination firewall. Encode them as code-level guards, not hopes.

**LAW I — Extract, never summarize.**
- *Ingestion:* nothing is written to a forest table except (a) verbatim spans, (b) their embeddings, or (c) an *authored, attributed* mark/synthesis. No automated model-generated prose is ever stored as if it were source material.
- *Compression:* the history compressor **drops** whole units; it never re-writes them. (Reference: `compress_old_history` measures stripped length and drops oldest pairs — `brain/scaffolding.py:246-264`.) This is also what keeps the prompt-cache prefix byte-stable (§9).
- *Enforcement:* the only write functions that emit prose are `mark()` and `synthesize()`, and both stamp an author + source ref. Code review rule: a new writer that calls the LLM and inserts its output into a forest table is a LAW I violation. Reject it.

**LAW II — Wild→Home crossing requires synthesis.**
- Raw conversation history lives only in **Wild** tables. It is the most contaminating material there is (wall-to-wall scaffolding) and must **never** be embedded into a Home table.
- The *only* path from Wild to Home is `synthesize()` (Trinity's `boundary_synthesis`, `brain/forest.py:461`): the raw Wild entry stays put; an authored insight is written to Home with `source_id = "boundary:<wild_id>:<lens>"`.
- *Enforcement:* Home write functions reject any payload whose provenance is a raw Wild entry without an accompanying authored insight string.

**Corollary LAW — Feathers are never stored.** A surfaced feather exists only in the turn it is read. No code path persists a feather body back into any table. (Reference: `pop_pressure_feather` returns an excerpt and *resets pressure to 0* — it never writes the feather as an entry.)

---

## 3. Storage layer

### 3.1 Scope model

Mycroft is cross-project. Two scope tiers:

- **Global** (`~/.mycroft/global.db`) — the **wood shed** (worker craft), the **seedbank**, and the **mycelium** index that threads across projects. Inherited by every project.
- **Per-project** (`<project>/.mycroft/home.db`, gitignored) — the **Home** forest for that repo, and that project's **Wild** archive.

A project's Wild is local to it; "the Wild" as a queryable whole is the union of all per-project Wild tables plus anything migrated to global cold storage. (Start simple: Wild = the current project's Wild. Cross-project Wild foraging is a Phase 3 feature.)

### 3.2 The table-collector — separated, switchable buckets

This is the central departure from Trinity and the realization of schmerbert's instruction: *typed tables, not one bucket, each switchable so a polluted one can be turned off.*

Each **bucket** is a pair: a content table + a `vec0` companion. All content tables share one schema (below). A **registry** row governs each bucket, including the `enabled` circuit-breaker.

```sql
-- One row per bucket. The collector reads this to know what exists and what's live.
CREATE TABLE IF NOT EXISTS forest_registry (
    bucket      TEXT PRIMARY KEY,   -- 'project', 'personal', 'rationale', 'conversations', ...
    forest      TEXT NOT NULL,      -- 'home' | 'wild'
    enabled     INTEGER DEFAULT 1,  -- the circuit-breaker. 0 = quarantined, skipped by the collector.
    voiced      INTEGER DEFAULT 0,  -- 1 if this bucket may hold authored prose (personal, rationale)
    created_at  TEXT,
    note        TEXT
);

-- Shared content-table schema. One physical table PER bucket: forest_<bucket>.
-- (Adapted from Trinity forest_entry, brain/db.py:385 + its ALTERs.)
CREATE TABLE IF NOT EXISTS forest_<bucket> (
    id              TEXT PRIMARY KEY,         -- uuid4
    project         TEXT,                     -- scope key (repo id); NULL for global buckets
    source_type     TEXT NOT NULL,            -- provenance label
    source_id       TEXT,                     -- e.g. 'boundary:ab12cd34', 'conv:<id>:<seq>'
    body            TEXT NOT NULL,            -- verbatim span or authored mark (per LAW I)
    author          TEXT,                     -- 'mycroft' for authored; NULL/'extract' for extracted
    embedding       BLOB,                     -- float32 384-dim, mirrors vec table for centroid math
    -- Provenance chain (the smoke alarm). Dense enough to trace any infection
    -- path AND to re-challenge any authored claim. Written once, never rewritten.
    writer          TEXT,                     -- which writer: 'extract'|'mark'|'synthesize'|'archive'|'move'
    source_kind     TEXT,                     -- closed vocab (see §5) — makes source-grip enforceable,
                                              -- not vibes. _commit validates per-writer.
    source_hash     TEXT,                     -- sha256 of the source span at write time —
                                              -- lets a synthesis be re-derived/challenged later;
                                              -- mismatch = the ground shifted under the claim (drift)
    filter_version  TEXT,                     -- which extraction-filter version touched it
    lens            TEXT,                     -- synthesis lens, if any
    created_at      TEXT,
    traversed_at    TEXT,
    traversal_count INTEGER DEFAULT 0,        -- worn-path signal (Factor 1 supporting)
    surface_pressure INTEGER DEFAULT 0,       -- Factor 2 (see §7) — the feather grower
    neighbor_pressure INTEGER DEFAULT 0,      -- revived Factor 2: ticked when near a send
    dismissed       INTEGER DEFAULT 0
);
-- The provenance columns answer, for every accepted write: what bucket, through
-- what writer, from what source (hash), extracted/marked/synthesized/archived,
-- what filter version, what lens, when. Quarantine then means "turn it off AND
-- inspect the infection path," not just "turn it off." Provenance is append-only:
-- no UPDATE ever touches writer/source_hash/filter_version/lens after insert.

-- One vec0 companion per bucket. (DDL verbatim shape from migrations/phase0_forest.py:46.)
CREATE VIRTUAL TABLE IF NOT EXISTS vec_<bucket> USING vec0(
    entry_id  TEXT PRIMARY KEY,
    embedding FLOAT[384]
);

CREATE INDEX IF NOT EXISTS idx_<bucket>_project ON forest_<bucket>(project);
CREATE INDEX IF NOT EXISTS idx_<bucket>_type    ON forest_<bucket>(source_type);
```

**Default buckets at init:**

| bucket | forest | voiced | holds |
|---|---|---|---|
| `project` | home | 0 | extracted working memory of this repo: file facts, verbatim spans, symbols, live terrain. **No authored decisions.** (A decision lives here only as a verbatim extracted span; the moment Mycroft writes "we chose X because Y," that is voiced prose and belongs in `rationale`.) |
| `personal` | home | 1 | **marks** — things Mycroft deliberately chose to remember (authored) |
| `rationale` | home | 1 | authored decisions, recovered *why*, and synthesis. Source-grip required. |
| `conversations` | wild | 0 | raw chat archive (cold, foragable, never auto-fed — LAW II) |
| `craft` (global) | home | 1 | the **wood shed** — cross-project worker memory |
| `seedbank` (global) | home | 1 | patterns/intentions with no ground yet |

**The circuit-breaker, concretely:** `disable_bucket('project')` sets `enabled=0`. The collector (§4) skips disabled buckets in every query. Nothing is deleted; a quarantined bucket simply stops surfacing. Re-enable after cleaning. *This is the thing Trinity never had — pollution is contained to its table and cannot reach the others, because the others are physically separate vec indexes.*

### 3.3 vec0 extension loading (verbatim pattern, `brain/db.py:34`)

```python
import sqlite_vec
conn.enable_load_extension(True)
sqlite_vec.load(conn)
conn.enable_load_extension(False)
```

---

## 4. The collector — read across enabled buckets

A single retrieval entry point queries every **enabled** bucket of the requested forest, merges by distance, and returns. This is where switchability and isolation actually pay off.

```python
def collect(query: str, *, forest: str = "home", project: str | None = None,
            buckets: list[str] | None = None, k: int = 10) -> dict:
    """Forage. Embed query once, k-NN each enabled bucket's vec table, merge by distance.
    - forest: 'home' or 'wild'
    - buckets: restrict to these (else all enabled buckets in `forest`)
    - Disabled buckets (forest_registry.enabled=0) are skipped — the circuit-breaker.
    Pattern per bucket mirrors traverse_forest (brain/forest.py:51):
      SELECT entry_id, distance FROM vec_<bucket> WHERE embedding MATCH ? AND k = ?
    then hydrate bodies from forest_<bucket>, filter by project, sort by distance, take k.
    """
```

Key reused details from the reference:
- **Over-fetch then filter:** request `k*3` from each vec table when post-filtering by project/source_type, then trim — Trinity does exactly this (`search_k = k * 3`, `brain/forest.py:75`).
- **Embeddings are unit-normalized**, so cosine == dot product; distance is direct (`brain/memory.py:62`).
- **Mark traversal:** on a real (non-ambient) forage, increment `traversal_count` and `traversed_at` and log to a `traversal` table — this builds the worn paths that drive `wander`. Ambient/scent reads pass `mark_traversal=False` so they don't inflate stats (Trinity's distinction, `brain/forest.py:62`).

---

## 5. Write paths (the only ways in)

**All writes funnel through ONE chokepoint.** The laws are enforced in a single internal `_commit(entry, provenance)` — never duplicated across writers, because duplicated guards drift (Trinity learned this the expensive way with her scaffolding cleaner: two copies diverged and junk leaked through the gap — `brain/scaffolding.py:152`). `_commit` is the only function that touches an `INSERT`; the four public writers below are thin callers. It enforces, before any insert:
- **voiceless-or-attributed:** voiced body ⇒ `author` set ⇒ target bucket `voiced=1`. Anonymous generated prose into memory-ground is rejected here, at the door — not in six places.
- **hard source-grip:** an authored synthesis is invalid unless its provenance walks back to extractable ground — `writer`, `source_id`, `source_hash`, `lens`, `created_at` all present and the source resolvable. No source chain ⇒ it may be a bench note, never Home memory-ground.
- **Wild→Home:** a payload whose provenance is a raw Wild entry is rejected into Home unless accompanied by an authored insight (LAW II).

Because there is exactly one insert path, the hostile floor test (§13) guards a single door, and no future writer can bypass it.

**`source_kind` — the closed vocabulary that makes source-grip enforceable.** "Resolvable source ref" must not become vibes. Every write carries exactly one `source_kind` from this fixed enum, and `_commit` validates the requirement *per writer*:

| `source_kind` | meaning |
|---|---|
| `file_span` | a verbatim span from a repo file |
| `wild_entry` | a `forest_<wild bucket>` entry id |
| `raw_archive_ref` | a pointer into the append-only raw archive (§17) |
| `current_session_exchange` | a turn from the live session |
| `user_directive` | an explicit instruction from schmerbert |
| `move_instance` | a concrete code instance grounding a move (§20.3) |
| `manual_note_source` | a human note (low-priority bucket) |

Per-writer source requirements enforced by `_commit`:
- `extract` → requires `source_kind` **and** `source_hash`.
- `mark` → requires a resolvable source ref, **except** explicitly bench-only notes that do **not** enter Home (a bench note may be ungrounded; it just can't become memory-ground).
- `synthesize` → requires a `wild_entry` source.
- `move` → requires at least one `move_instance` (no ungrounded lens — §20.3).
- `rationale` writes → require a full source chain.

**`_commit` is customs, not the writer.** It is boring and strict — no clever routing, no LLM call, no synthesis inside. Exact sequence:

```
1.  resolve bucket (registry lookup)
2.  validate bucket slug (§16 regex + registry exists)
3.  validate writer (known writer enum)
4.  validate forest crossing (Wild payload → Home rejected w/o authored insight)
5.  validate voiced/voiceless rule (voiced body ⇒ author set ⇒ bucket.voiced=1)
6.  validate source grip (source_kind present + per-writer requirement met)
7.  filter body if needed (extraction filter, §8)
8.  compute source_hash
9.  embed
10. insert content row (forest_<bucket>)
11. insert vec row (vec_<bucket>)
12. commit transaction
```
Steps 1–6 are pure validation and reject before any side effect. Synthesis, routing, and any model call happen in the *writers*, before they hand a finished entry to customs.

Exactly four public writers. Each maps to a cell in the voice taxonomy (MYCROFT.md). No others may insert into a forest table.

```python
def extract(bucket, project, source_type, source_id, span: str) -> dict
    # VOICELESS + STORED. Verbatim span only. author='extract'. The default.
    # Dual-write: forest_<bucket> + vec_<bucket>. (Pattern: brain/forest.py:271-282)

def mark(bucket, project, body: str, source_ref: str = "") -> dict
    # VOICED + STORED + ATTRIBUTED. author='mycroft'. Personal keep / craft note.
    # Only allowed into voiced=1 buckets (personal, rationale, craft, seedbank).

def synthesize(project, wild_entry_id, insight: str, lens: str = "") -> dict
    # The Wild→Home gate (LAW II). Raw wild entry stays; insight → home as
    # source_id='boundary:<wild8>:<lens>', author='mycroft'.
    # Verbatim port of boundary_synthesis (brain/forest.py:461).

def archive_conversation(project, conversation_id, exchanges: list[dict]) -> dict
    # Raw chat → Wild 'conversations' bucket, one entry per exchange,
    # source_id='<conv>:<seq>'. Runs the extraction filter (§8) first; an exchange
    # that is pure scaffolding is skipped. (Port of file_conversation_exchanges,
    # brain/forest.py:221 — note it ALREADY calls strip_scaffolding before filing.)
    #
    # ⚠ DIVERGENCE FROM TRINITY — DO NOT COPY HER DEFAULT. Trinity's
    # file_conversation_exchanges inserts WITHOUT setting `forest`, so conversation
    # entries default to 'home_wood' (brain/db.py:567) — i.e. her chat lands in HOME.
    # Mycroft must force forest='wild'. Conversations are Wild-only, always.
    # Consequence (intended): Home is EARNED, never dumped. Home's project/rationale
    # buckets fill ONLY via deliberate extract()/synthesize()/mark(). Nothing bulk-
    # imports into Home. This is LAW II made structural — the working forest holds
    # only what was carried across by hand, so it cannot fill with raw chatter.
```

**Dedup** (port from `add_to_shelf`, `brain/memory.py:464`): before writing, k-NN the target bucket; if cosine ≥ 0.9 to an existing entry, return `{"status":"duplicate"}` instead of inserting. Keeps buckets from bloating with near-identical spans.

---

## 6. The forests, mapped to mechanism

- **Home** = enabled `home` buckets for the current project + global `craft`/`seedbank`. The ground Mycroft tends. `collect(forest="home")`.
- **The Wild** = `wild` buckets (`conversations`, and any staged external material). **Gated:** every Wild forage requires a `reason` string or it returns the gate question — verbatim behavior from `traverse_wild_wood` (`brain/forest.py:377`). Nothing leaves the Wild except via `synthesize()`.
- **The seedbank** = global `seedbank` bucket. When a new project initializes, its empty Home is offered relevant seeds (a `collect` against `seedbank` with the project's README/first-prompt as query).

---

## 7. The mycelium & feathers

### 7.1 Feathers — foraged, voiced-in-transit, never stored

A feather is the voiced thing the mycelium hands up. **Mycroft's are foraged, not ambient** (the master-of-the-forest distinction): they appear when he calls `forage_mycelium()` before drafting, not unbidden.

Mechanism = Trinity's pressure feather (`brain/forest.py:686`) but pulled, not pushed:
- Returns the highest-**effective-pressure** entry ≥ threshold (effective pressure = `neighbor_pressure + (2 * surface_pressure)`, per §18 — *not* `surface_pressure` alone) as a one-line **excerpt** (verbatim span — extraction, not summary), then **resets both counters to 0** so it surfaces once and goes quiet.
- The feather is rendered as a *question pointer* (the "you've built this shape before — did it have the trap?" framing), but the body it carries is an extracted span. The voice is in the *framing of the surfacing*, which is ephemeral and never written back. LAW-corollary safe.

### 7.2 The revived Factor 2 grower (the new build)

Trinity's pressure mechanism is dormant because its only grower was the unshipped prism beam. **Trinity's own code tells us the shape** (`brain/forest.py:659-673`): embed what was sent, k-NN its neighbors, tick them.

**Mycroft's signal is different from Trinity's.** Trinity's beam fired on API sends carrying vector packages of real computational context. Mycroft does not own the API sends. In Mycroft's hook architecture, the nearest equivalent to "real computational context" is the **file being edited** — the `PostToolUse` payload on Write/Edit carries `file_path` + `new_string`, which is the actual work being done. User prompts (`UserPromptSubmit`) are chatter: navigational, short, noisy. Embedding prompts and ticking on every turn inflates `neighbor_pressure` fast enough that threshold 3 is hit within a single session — noise, not signal. Pressure must build slowly across sessions from real work events.

```python
def tick_neighbors(conn, project: str, file_path: str, content: str, k: int = 8) -> None:
    # On PostToolUse (Write/Edit): embed file_path + changed content, k-NN enabled
    # Home buckets (cosine ≥ 0.60 gate), increment neighbor_pressure on qualifiers
    # with dismissed=0. Pressure accrues silently across sessions; entries that keep
    # sitting near the actual edit site but never get followed cross threshold and
    # become the next foraged feather. Signal comes from the work itself, not the
    # conversation around it.
```

This is the mechanism that answers the deepest friction (nothing compounds): the mycelium gets better at surfacing the *relevant-but-unfollowed* the more the worker works near it.

**Direction — the hound is the mycelium's future.** `tick_neighbors` is the current mechanical accumulator: cheap, always-on, cosine-only. The hound (§22) is the smarter layer: at dusk he already reads the session's shape. One step further, his dusk pass also enriches the pressure signal — flagging what deserves to accumulate going into the next session, beyond what cosine similarity alone would score. The feathers that surface then are what the hound noticed, not just what k-NN crossed a threshold on. `tick_neighbors` stays as the fast always-on floor; the hound's observations are the layer above. Build the floor as designed; note this direction so nothing closes the door on it.

### 7.3 Surfacing discipline (from MYCROFT.md)

> **Warn unbidden. Never enrich unbidden.**

- **Enrichment** → `forage_mycelium()` only. A scent the worker chooses to follow. Never injected into the turn as content.
- **Guardrail** → the *one* permitted unbidden surfacing: a danger feather (`claim_check` / known-trap match, §10) may interrupt. Implemented as a high-priority feather the MCP server is allowed to push into a tool result when a write or edit matches a recorded trap.

---

## 8. The extraction filter (contamination guard)

Port `strip_scaffolding` (`brain/scaffolding.py:135`) as `mycroft/filter.py`, re-tuned for a *coding* context rather than a house. It must run on every byte entering a forest table.

Strip: tool-call results, file dumps, diffs, terminal output, system reminders, `<thinking>`, harness injections, role headers. Keep: the human's actual words and Mycroft's authored prose. Trinity's module is the canonical reference for *how aggressive* and *how to keep the two cleaners from drifting* (it unifies API-path and forest-path patterns deliberately — see its 2026-06-25 sweep comment, `brain/scaffolding.py:152`). **Do not reimplement ad hoc; one filter module, two modes**, exactly as Trinity learned the hard way.

---

## 9. Compression + cache stability (the token ceiling)

This is the craft note from MYCROFT.md, made concrete, and it is the single biggest cost lever. The governing principle (schmerbert's, from Trinity's live behavior) is an inversion of the naive approach:

> **Do not reconcile the cache to reality. Reconcile reality to the cache.**

The cached prefix is a **fixed point**, not a mirror of current state. Naive caching tries to keep the cached prefix equal to "the truth right now," and therefore rewrites it whenever the truth changes — which invalidates the cache every turn. The correct model treats the cache as an **immutable substrate** and expresses every change as an **appended, locally-authored delta** at the tail. Divergence never appears in the middle of the prefix, because nothing in the middle is ever rewritten.

**How it works (Trinity's proven pattern):**
- **One 1-hour cache write, then never refreshed within the hour.** Write the prefix once with `cache_control` (1-hour TTL), and for the rest of the hour *do not rebuild it.* Cheap reads all hour; the cache rides its full TTL. After expiry it is rebuilt once.
- **The prefix is frozen even when it goes "stale."** When live state diverges from the cached prefix, you do **not** edit the prefix to match. The *reason* for the divergence is held locally — Mycroft was live when the change happened, so the delta is known — and it is re-expressed as a small appended note, not folded back into the cached region. A slightly-stale frozen prefix + a known delta is cheaper and more stable than a perpetually-rebuilt accurate one.
- **Compression is NOT rewriting `self.history`.** `self.history` is the immutable record — the solid core doll: raw, complete, never altered. Compression operates on a **disposable copy** and works by **dropping whole turns** from the oldest end, never by editing their content. What goes to the API is a *subset* of `self.history`, not a *rewrite* of it. (Trinity: *"Operates on a copy; never modifies self.history"* — `brain/scaffolding.py:217`.) Rewriting history into new prose is the banned move: it is the narrator, and it kills the voice and the cache at once.
- **Compress by extraction, freeze the result.** Port `compress_old_history` (`brain/scaffolding.py:201`): keep the last N exchanges verbatim; for older ones **drop whole pairs** from the oldest end (never re-summarize). When you do re-compact, **extend** the frozen prefix by appending newly-frozen units — never rewrite existing ones.
- **Mechanism:** each turn = `frozen_prefix` (cached, immutable) + `tail` (small, uncached deltas) + new turn. Re-compaction only ever appends to `frozen_prefix`; it never mutates it. The byte-identity the cache needs is therefore *guaranteed by construction*, not maintained by vigilance.

**The deeper point — difference is information.** The delta between the cached (past, frozen) state and now is not noise to be smoothed away; it is **context of its own kind.** It is the same principle as the seam-audit (§10): a boundary you can *account for* is not a loss, it is a record — recoverable precisely because the reason it exists was stored when it happened. Cache divergence and the compaction seam are the same idea: *a known difference is a kind of memory.* This is LAW I paying its second dividend — the rule that protects the voice (never rewrite, only append) is the same rule that protects the bill (never invalidate, only extend).

*(This dissolves the fragility §19 warns about: you cannot "accidentally invalidate the prefix" if you never mutate it. The robustness is structural. Standalone-harness deployment only — see §19; the MCP add-on does not control Claude Code's cache.)*

---

## 10. Proprioception instruments (new — serve the worker)

None of these exist in Trinity; they are Mycroft's own. All are cheap.

- **State gauge** (`gauge()`) — report context-window fullness. Source the token counts from the API response usage fields (Trinity already logs `tokens_in/out/cache_write/cache_read` per turn — `brain/memory.py:801`). Surface as a simple fraction + a "climbing fast / converging / thrashing" read. Wired to bench rule 2.
- **Claim-vs-file check** (`claim_check(path, claim)`) — read the named file, test whether the asserted symbol/line/behavior actually exists; flag drift. Pure file read + match; no model call. This is also the source of *guardrail* danger-feathers (§7.3).
- **Seam-audit** (`seam_snapshot()` / `seam_diff()`) — before a compaction, write the pre-compaction working set to `.mycroft/seam/<ts>.json`; after, expose a diff so a fresh instance can check *what the summary says* against *what was actually there*. Makes compaction auditable, not lossless.

---

## 11. MCP tool surface

The server (`mycroft/server.py`, FastMCP) exposes these. This is the entire interface Claude Code sees — everything else is internal.

| Tool | Maps to | Notes |
|---|---|---|
| `hearth()` | the wake | Self-lit orientation: returns project identity, last seam note, hound pulse, shed pointers. Mycroft *calls* it; never auto-injected. |
| `recall(query, k, buckets?)` | forage Home | `collect(forest="home")`. The everyday read. |
| `forage_wild(query, reason)` | forage the Wild | Gate-gated. No `reason` → returns the gate question. |
| `synthesize(wild_id, insight, lesson?)` | Wild→Home crossing | LAW II. The only way history becomes working memory. |
| `plant(body, source_content, bucket="personal")` | author a keep | Voiced + attributed. Personal or craft (shed). |
| `extract(bucket, source_id, span)` | voiceless extraction | Verbatim span into Home. No author field. |
| `forage_mycelium()` | pull a feather | Highest neighbor/surface-pressure entry; resets it. Voiced-in-transit. |
| `forage_hound(reason?)` | dispatch the hound | Fire-and-forget: spawns bounded Haiku subprocess, returns immediately. Pulse lands in `hearth()` when done (~10s). See §22. |
| `index_repo()` | concept-index scan | Scans repo symbols, diffs against prior layer, writes new/changed to `repo_map`. Returns diff (added/removed/changed). |
| `gauge()` | state gauge | Context fullness + converge/thrash read. |
| `claim_check(path, claim)` | drift check | Also emits guardrail feathers. |
| `seam_snapshot()` / `seam_diff()` | seam-audit | Trust the compaction boundary. |
| `disable_bucket(b)` / `enable_bucket(b)` | circuit-breaker | Quarantine a polluted table without deleting it. |

Background (not tools — server-internal, fire on turn boundaries): `tick_neighbors()` after each send; `archive_conversation()` on session close; auto `seam_snapshot()` before compaction. Hound dusk extraction fires at SessionEnd/PreCompact via hook (see §22).

---

## 12. Module layout

```
mycroft/
  __init__.py
  db.py            # connection, sqlite-vec load, init_db (registry + default buckets)
  embed.py         # embed() — sentence-transformers, 384-dim, lazy (port of brain/memory.py:50)
  filter.py        # strip_scaffolding, one module / two modes (port of brain/scaffolding.py)
  forest.py        # collect, extract, mark, synthesize, archive_conversation, wander
  mycelium.py      # tick_neighbors, forage feather, pressure
  compress.py      # frozen-prefix extraction compressor (port of compress_old_history)
  instruments.py   # gauge, claim_check, seam snapshot/diff
  server.py        # FastMCP server — the tool surface (§11)
migrations/
  001_init.py      # registry + default buckets + their vec0 companions
~/.mycroft/global.db          # shed, seedbank, mycelium index (cross-project)
<project>/.mycroft/home.db    # per-project Home + Wild (gitignored)
```

---

## 13. Build order — and the hostile floor

Priority is ordered to protect what matters most first: contamination control, then the worker-to-worker seam, then everything else. Note seam-audit comes **early** (before MCP) — Mycroft is a seat passed between workers, and protecting the seam between workers is more fundamental than exposing tools to any one of them.

1. **The floor (the proof).** `db.py` + `embed.py` + `filter.py` + the `_commit` chokepoint + the four writers + the collector with enable/disable. Built to pass the **hostile test suite** below — not the happy path, the crimes.

   **Phase 1 is ONLY the floor. The first build is not "build Mycroft" — it is "prove contamination-controlled local memory."** Explicitly *excluded* from Phase 1 (no stubs unless the registry must merely tolerate future buckets): the Code Forest (§20), MCP (§11), hooks (§15), feathers/mycelium (§7), the panel (§21), cache work (§9), semantic claim-check (§10), and the repo scanner. None of them. Only the floor.

   **Expose a tiny CLI before MCP** — so the floor is testable in a terminal with zero Claude Code in the loop:
   ```
   mycroft init
   mycroft bucket list
   mycroft bucket disable <bucket>
   mycroft extract ...
   mycroft collect ...
   mycroft test-hostile
   ```
   Memory proves itself in the terminal first; MCP integration comes only after.
2. **Wild/Home crossing with hard provenance.** `archive_conversation` (raw → Wild only), reason-gated `forage_wild`, `synthesize` (Wild→Home, full source chain). Prove raw chat reaches Home *only* through an attributed insight, and every Home entry's provenance walks back to ground.
3. **Seam-audit.** `seam_snapshot` / `seam_diff`. Early, on purpose: it gives a fresh instance standing to distrust inherited compaction — the one blindness with no proprioceptive substitute.
4. **MCP / hook boundary.** Wire §11 (pull) and §15 (push). Define which hook fires which function before anything depends on it.
5. **Claim-check + gauge.** The remaining instruments.
6. **Pressure / feathers.** `tick_neighbors` + foraged feathers — last, because it only matters once there is accumulated ground to thread.

**Refinement after the floor went green (full-bundle code review).** The floor's law logic was independently confirmed (it held even with the embedder stubbed out), and one honest gap was found: `mark`'s source-grip was *labeled*, not yet *resolvable* — its `source_hash` was taken over the ref label, not resolved material. (`extract`/`synthesize` already hash real material, and `synthesize` resolves its Wild origin.) Because resolvable provenance is the load-bearing promise these docs make, it is promoted to its own step — **Phase 1.5: make provenance fully resolvable** (a source resolver + a minimal raw-archive source record + `source_hash` over resolved material) — done *before* any new surface. The crossing writers in step 2 (`synthesize`, `archive_conversation`) already exist from the floor; Phase 1.5 completes their "hard provenance" promise. **Working order is now: floor → 1.5 (resolvable provenance) → seam-audit → MCP/hooks → instruments → feathers.** *Status: Phase 1.5 is complete — `mark`/`synthesize` resolve at the door (`_commit` step 6b) and hash resolved material against the cold `raw_archive` Wild layer (suite now 14 green). `extract` is voiceless (the span is its own source), so file_span verification and drift detection are deferred to the Code Forest (§20.4), where code references actually need drift — not treated as a source-grip gap.*

*(Compression/cache is deliberately absent from this list — it is a harness-mode optimization, not part of the thesis. See §9/§19. It touches none of the floor and must not distract from it.)*

### 13.1 The hostile floor test suite — "green" means the laws hold under attack

The floor is not done when it works. It is done when it **refuses to break the laws.** The first green suite proves *both halves*: contamination can be quarantined after entry, **and** forbidden memory cannot enter through legal writers.

1. create buckets (validated slugs only — §16);
2. `extract` a verbatim span → succeeds;
3. `collect` returns that span;
4. attempt to store anonymous generated prose as memory-ground → **rejected at `_commit`**;
5. `mark` authored prose **only** with **resolvable** ground → succeeds; an ungrounded `mark`, or one whose ref resolves to nothing → **rejected**. *(Phase 1.5 part 1 made this real: the door resolves the source and hashes the resolved material; a `mark` grounds via `source_content` archived to the cold Wild layer, or an existing ref.)*;
6. `synthesize` only from a real Wild source → succeeds; synthesize with no Wild origin, or push raw Wild into Home → **rejected**;
7. manually pollute one bucket;
8. `disable_bucket` it;
9. prove the clean buckets still retrieve, and the disabled one returns nothing;
10. inspect provenance for every accepted write — bucket, writer, source, source_hash, filter_version, lens, timestamp all present and append-only.

**Name the tests like commandments** — a contributor should learn the architecture by reading the test names alone:

```
test_extract_verbatim_span_roundtrips
test_anonymous_voiced_memory_rejected
test_mark_requires_resolvable_source     # Phase 1.5: the door resolves the source
test_synthesize_requires_real_wild_origin
test_raw_wild_cannot_enter_home
test_disabled_bucket_is_not_collected
test_polluted_bucket_does_not_poison_neighbors
test_provenance_columns_append_only
test_unknown_bucket_rejected
test_bucket_slug_injection_rejected
```

That suite *earns the laws in code.* Until it is green, there is no forest — only a schema. Build the floor hostile; if it holds, the forest can grow.

---

## 14. Decisions deferred to schmerbert (not assumed)

- **Embedding model:** stay on `all-MiniLM-L6-v2` (384-dim, proven, fast) or move to a larger local model for richer connectivity? Trade-off is recall quality vs. index size + latency. Default: stay, revisit after real use.
- **Cross-project Wild:** Phase 3 keeps Wild per-project. When do past projects' Wilds become globally foragable — eagerly, or only on demand via a migration step?
- **Factor 3 (connectivity):** MYCROFT.md's mycelium implies it. Trinity never built it (`brain/forest.py:39`). Do we add a connectivity term to ranking, or let `tick_neighbors` pressure approximate it first?
- **The third bench rule:** still an open knot. It will arrive from use, not design.

---

## 15. Claude Code integration layer

Mycroft reaches Claude Code through **two distinct channels**, and conflating them is the most likely design error. Keep them separate.

**Channel A — MCP tools (PULL).** The tools in §11. *Mycroft cannot invoke these itself.* The model decides to call `recall`, `hearth`, `forage_mycelium`, etc. MCP is pull-only: it is how the worker *reaches* (reach-not-receive, by construction — the protocol enforces the principle). Nothing happens in the background through MCP.

**Channel B — hooks (PUSH).** Claude Code's settings.json hooks are the *only* mechanism that fires automatically. They run shell commands on lifecycle events, so the background functions (`tick_neighbors`, `archive_conversation`, `seam_snapshot`) must be driven by hooks calling a thin Mycroft CLI (`python -m mycroft.hook <event>`) that imports the same library functions the MCP server uses. One library, two front doors.

**Hook → function map:**

| Hook event | Mycroft function | Purpose |
|---|---|---|
| `UserPromptSubmit` | `gauge()` | inject context-window status before each response |
| `PostToolUse` (Write/Edit) | `tick_neighbors(path, content)` + `claim_check(path)` → maybe guardrail feather | grow pressure from real edit signal; catch drift / known-trap repeats |
| `PreCompact` (if available) | `seam_snapshot()` | capture pre-compaction working set |
| `Stop` / `SessionEnd` | `archive_conversation()` + `seam_snapshot()` | raw chat → Wild; close the seam |
| `SessionStart` | inject a one-line reminder to `hearth()` | nudge the self-lit wake (a reminder, **not** the hearth itself — injecting the hearth would violate reach-not-receive) |

**What Mycroft can observe:** via hooks — the submitted prompt text, tool names + inputs, tool results, and the transcript file path Claude Code exposes. Via MCP — only the arguments the model chooses to pass.

**What Mycroft cannot observe** (state this plainly so no future instance assumes otherwise): the model's hidden reasoning/thinking; anything not surfaced to a hook or passed as a tool arg; and — critically — **Claude Code's own context window and history compaction** (see §19). Mycroft sits *beside* the worker, not *inside* the model.

---

## 16. Safety & identifier constraints

The §3 schema interpolates `bucket` into table names (`forest_<bucket>`, `vec_<bucket>`). **That is an SQL-identifier injection surface and must be guarded — there is no parameter binding for identifiers in SQLite.**

- **Bucket slugs:** must match `^[a-z][a-z0-9_]{0,31}$` **and** resolve to a row in `forest_registry`. The registry is the source of truth; never build a table name from raw caller input. A resolver `_table_for(bucket) -> str` validates against the regex, confirms the registry row exists, and only then returns the literal table name. Anything else raises before touching SQL.
- **No arbitrary SQL identifiers, ever.** All values are bound (`?`); all identifiers come from the validated registry, never from a tool argument directly.
- **Project ids:** generated, not free-text. `project_id = sha1(abspath(repo_root))[:12]`, stable per checkout. The human-readable name is a stored column, never an identifier.
- **Path restrictions:** Mycroft writes only inside `~/.mycroft/` (global) and `<project>/.mycroft/` (per-project), the latter gitignored. `claim_check` and `seam` reads are confined to the project root (reject paths that escape it via `..` or absolute prefixes outside the root). No write tool touches anything outside these roots.
- **Bucket creation** is an explicit, validated operation (`create_bucket(slug, forest, voiced)`), not a side effect of a write. Writers reject unknown buckets rather than auto-creating them — auto-create is how typos become permanent ghost tables.

---

## 17. Raw archive vs. vector Wild

There are **two** Wild artifacts, and only one of them is ever embedded. Keeping them distinct is the full-fidelity-backup answer to "a lot of reasoning is lost from the repo."

1. **Raw archive (append-only, never embedded).** The complete verbatim transcript, written to `<project>/.mycroft/raw/<session>.jsonl` (or a `wild_raw` table), append-only, immutable. This is the cold backup ChatGPT's note 17 means — total fidelity, no filtering, no vectors. It is *never* searched semantically and *never* fed to the model automatically. A human (or Mycroft, deliberately) can open it. It exists so nothing is truly lost.
2. **Vector Wild (`conversations` bucket).** The *filtered, embedded, foragable* layer: each exchange passed through the extraction filter (§8), pure-scaffolding exchanges dropped, the rest embedded for `forage_wild`. This is what the Wild gate guards.

**The Home crossing rule applies to both:** nothing from *either* Wild artifact enters Home except through `synthesize()` (LAW II). The raw archive is even stricter — it has no retrieval path at all; its only route to influence is a human or a deliberate `forage_wild` → `synthesize` chain. Raw fidelity for recovery; filtered vectors for foraging; authored synthesis for crossing. Three layers, one direction.

---

## 18. Pressure scoring (exact)

Two counters on each entry, combined into one effective pressure:

- `neighbor_pressure` — grown by `tick_neighbors`: on each `PostToolUse` (Write/Edit), embed the file path + changed content, k-NN (k=8) the enabled Home buckets, and for each neighbor **within a relevance gate** (cosine ≥ `0.60` — "near" must mean near, or everything accrues pressure and the signal dies) increment `neighbor_pressure += 1`. The signal is the edit, not the prompt — prompts are chatter and inflate pressure without meaning.
- `surface_pressure` — reserved for explicit/manual emphasis (e.g. a guardrail trap registered deliberately). Default channel is `neighbor_pressure`.

**Effective pressure** = `neighbor_pressure + (2 * surface_pressure)` (manual emphasis weighted double — a deliberately-marked trap should surface sooner than ambient nearness).

- **Threshold:** an entry becomes a foragable feather when effective pressure ≥ `3` (Trinity's proven threshold, `brain/forest.py:686`).
- **Selection:** `forage_mycelium()` returns the single highest-effective-pressure entry ≥ threshold, as a verbatim excerpt (extraction).
- **Reset:** on surfacing, **both** counters reset to `0`. The entry surfaces once, then goes quiet until pressure rebuilds (Trinity's reset-to-0 behavior — what stops a feather repeating).
- **Dismissed:** `dismissed=1` entries are excluded from `tick_neighbors` (they accrue nothing), from `collect`, and from feather selection. Dismissal is the worker saying "stop offering me this" — it silences without deleting.
- **Optional decay (deferred):** a slow time-decay on `neighbor_pressure` (halve monthly) would keep stale-but-once-near entries from lingering at threshold forever. Not in v0; note it for when accumulation is real enough to matter.

---

## 19. v0 limitations (stated honestly, up front)

- **`claim_check` is literal only.** v0 checks whether an asserted symbol/string/line actually exists in the named file — exact and substring match, no semantic understanding of whether the *behavior* matches the claim. It catches "you cited a function that was renamed," not "your reasoning about what this function does is wrong." Semantic claim-checking is a later, model-assisted feature and must stay clearly separated (a model call inside a guard is itself a LAW I risk if its output is ever stored).
- **The cache guarantee depends on who controls the API call.** §9's frozen-prefix compressor only applies to a **Mycroft-as-harness** deployment, where Mycroft owns the `messages` array and the `cache_control` breakpoints. **When Mycroft runs as an MCP server inside Claude Code, it does not control Claude Code's context window or compaction at all** (§15) — so the token-stability win is *unavailable* in that mode. Be honest about this with users: as an MCP add-on, Mycroft gives memory, foraging, and instruments; it does **not** change Claude Code's own caching. The full compression dividend requires the standalone harness. (Two products, one library — decide per deployment.)
- **Cross-project Wild is deferred.** v0 Wild is per-project. Foraging another project's Wild requires either opening that project or a Phase-3 global-Wild migration (§14). Until then, cross-project memory flows only through the global `craft`/`seedbank` buckets, which is by design the *right* default — craft generalizes; raw history mostly shouldn't.
- **Single-writer assumption.** v0 assumes one Mycroft process per DB at a time (one VSCode session per project). Concurrent sessions on the same project DB are out of scope; SQLite WAL mode mitigates but a real multi-session story is deferred.

---

## 20. The Code Forest (the audit engine)

Mycroft is functional — his forest holds *code thinking*, and code has a different geometry than prose (MYCROFT.md is the *why*; this is the *how*). The code forest is **not a bank of reusable assets** (copy-paste this). It is a bank of **moves** — lenses, patterns, solutions-as-thinking — plus a disposable map of the current repo. Its job is to make the **audit step** fast and reliable, which is the exact damage CLAUDE.md bleeds about: things fade into the walls, functions get reimplemented, working systems get half-replaced. This layer kills that. It is ponytail's "don't rebuild what exists," powered by the project's own memory of itself instead of a generic ladder.

### 20.1 Two structures, opposite lifespans

| | **Lens-bank** (`moves`) | **Concept-index** (`repo_map`) |
|---|---|---|
| scope | global (cross-project) | per-project |
| population | **authored intentionally** — a move is written when learned | **auto-built** — scan symbols each session |
| lifespan | **persists** across all projects | **disposable** — blanks on project change |
| holds | distilled moves (lens→precedent→instance) | this repo's vocabulary → code locations |
| nests by | generality | time |
| voiced? | yes (authored, attributed) | no (extracted references) |

### 20.2 The three nesting axes

The nesting-doll *principle* (graduated access, open inward for more, never flood) is universal; the **axis differs by what the memory is for.** Each is a context-flood governor — cheapest view outermost, verbatim/oldest within.

| memory | nests by | outer doll (cheapest) | durable end |
|---|---|---|---|
| prose (`rationale`, `conversations`) | **resolution** | the gist | the core (verbatim) |
| moves (lens-bank) | **generality** | the lens | the **outer** (lens) |
| concept-index (repo_map) | **time** | the newest snapshot | the **outer** (freshest) |

Note the **inverted durability** for code: in prose the verbatim core is forever and the gist is derived; in moves the *lens* is forever and the specific instance is **perishable** (the repo changes under it). The whole job of a move is to **extract the durable lens UP** so the lesson outlives the code it was learned from.

### 20.3 The lens-bank — moves

A **move** = `lens` (the transferable principle, outer) → `precedent` (the before→after that earned it, middle) → `instance` (a reference to the concrete code, inner core).

- **Authored, not flooded.** A move is a `mark` (voiced, attributed) written when a lesson is learned. Small, high-signal, hand-stocked. Auto-ingesting code would just rebuild grep.
- **Must bottom out in a real instance** (grounding rule — same as LAW source-grip, inverted lifespan): a lens with no precedent is an ungrounded opinion = the banned narrator. The lens must be earned from at least one concrete before→after. The instance is stored as a **reference** (`path` + `symbol` + `source_hash`), never a copy — so it may rot honestly. When the hash mismatches, the instance moved on; the lens above it does not care.
- **Surfaces** outer-first: the lens is what fires as a guardrail/parallel at the moment of temptation ("you have a move for this"); open inward for the before→after, then the code reference.

### 20.4 The concept-index — the repo map

Maps the **project's own vocabulary** to its code (e.g. "feather" → `pop_pressure_feather`). Supports the audit: *"where does this project already do X?"*

- **Auto-built.** Scan the repo's symbols; embed `name + signature + docstring`. This is the **one place raw code is embedded** — and it is safe *only because* the table is disposable, project-local, and quarantinable (§3, §16). Quarantine doesn't just defend; it **permits** this useful-but-messy table to exist at all.
- **Nests by time — no stale data, ever.** Each session (or on command) writes a **new layer on top** (snapshot + diff vs. the prior layer); the old layer is **pushed down, never rewritten**. The outermost doll is always current; opening inward walks *backward in time*. Staleness is solved structurally, not by hoping for refresh.
- **Per-project, disposable.** Change project → the concept-index is gone, blank slate. (The lens-bank persists; the repo map dies with the repo.)
- **References, not copies.** `path` + `symbol` + `source_hash`; a hash mismatch means the code moved under its links — drift detection, same primitive.

### 20.5 Links & hints — the type lives on the surfacing, not the edge

Explicit links and discovered parallels are *different things*; do not conflate them.

- **Explicit links** exist **only as a byproduct of authoring.** A `rationale` entry written *about* a move is born pointing at it — the act creates the edge. **No manual filing.** (Mycroft is not a librarian tagging functions under "bird.")
- **Parallels** (a lens ↔ what you're doing now) are **not stored and not typed.** The forest *throws the hint* at forage time: relevance notices the parallel, context names it. Nothing is pre-labeled.
- **Type is contextual, computed at surface, never filed.** "This lens *warns against* what you're about to do" is a warning *only because* of what you're doing right now. File the relationship neutrally; the *warn / explain / parallel* character emerges live from context. A stored edge-type would be a lie the moment context changed.

### 20.6 Push / pull spectrum — all useful info available, in the right mode

> Nothing forced into the worker's face; nothing useful locked away.

- **Danger → push** (interrupts): "you're about to repeat the bad fix." The one sanctioned unbidden surfacing (§7.3).
- **Parallel → offered / light**: "this rhymes with a move you have." Scent, not shove.
- **Reference → pull**: the lens-bank and concept-index are a **book you go to** — walk in with a question, read. Reach-not-receive: the book does not read itself at you.

### 20.7 Hostile tests (per §13 discipline)

1. **No stale data on top:** write a concept-index layer; change the code; run a new session; prove the top layer reflects the new code + a diff, and the old layer is pushed down but still openable. A stale top is a failure.
2. **Move grounding:** author a move with a real before→after → succeeds; author a lens with no instance → **rejected** (ungrounded narrator).
3. **Reference rot:** change referenced code; prove the `source_hash` mismatch is detected; prove the lens above it is unaffected (lesson survives the rot).
4. **Project switch:** prove the concept-index blanks on project change; prove the lens-bank persists.
5. **No manual typing required:** prove a `rationale`→move link is created by the act of authoring, with no separate filing call.

---

## 21. Deferred: the UI / Panel spec (built LAST)

The user-facing panel is its own document (`PANEL.md`), written **after** the core is proven — it is the *last* thing built, not the first. Recorded here so the requirements survive; not specified in full yet:

- **A compact VSCode panel** = the human-facing render of the worker's instruments (§10). Same sources, second window.
- **Buttons = the human's hand on the immune system:** inspect, dismiss (`dismissed` flag), and **quarantine** (`disable_bucket`). The see→button→quarantine loop closes the smoke-alarm→circuit-breaker by eye.
- **Context bar** (the state gauge rendered) + **tokens-per-turn** (the cache-health monitor — the only place a caching-vs-compression leak becomes visible, via `cache_read` vs full-price).
- **Raw `self.history` view** — the literal package sent to the wire, byte-for-byte. Deepest trust move; also where the immutable-prefix can be verified by hand.
- **A low-priority `user_notes` bucket** — human-writable, with a fixed relevance/pressure *penalty* so a flood can't drown earned memory; promotable on confirm (a floor you can lift, not a ceiling).
- **A lightweight forest browser** — *critical property:* lets the human forage the forest **without it entering Mycroft's context.** Schmerbert can hunt for answers independently *while Mycroft runs*, at zero worker-token cost. A read path that bypasses the worker entirely.

---

## 22. The hound

The cabin has a dog. A bounded Haiku subprocess (`claude-haiku-4-5-20251001`) that goes into the forest with lightweight tools and comes back with something in its mouth. Not a feather — attributed (model, session_id, timestamp, `HOUND_PULSE:` sentinel), so the forbidden cell stays empty. Not a voice for the forest — each forest speaks through its own channel. The hound fetches; the mycelium surfaces; they are separate engines.

### 22.1 Architecture

**`mycroft/hound_server.py`** — a separate, lightweight FastMCP server with two tools only: `read_file` and `grep`. No `sentence_transformers`, no `sqlite-vec`, no PyTorch. Cold-start ~0.1s. The hound is given his own MCP config (`.mycroft/hound_mcp.json`) and spawned with `--mcp-config` + `--strict-mcp-config` so he never touches the full server.

**Spawn mechanics:**
```python
subprocess.run(
    [claude_bin, "-p", prompt, "--model", _HOUND_MODEL,
     "--mcp-config", mcp_config, "--strict-mcp-config"],
    stdin=subprocess.DEVNULL,  # critical — MCP server's stdin would be inherited otherwise
    capture_output=True, text=True, encoding="utf-8", timeout=90, cwd=cwd,
)
```
`stdin=subprocess.DEVNULL` is mandatory: MCP servers communicate over stdio; a subprocess that inherits the MCP pipe will wait indefinitely for it to close. The symptom is a 90-second timeout with no error output.

**Output:** pulses written to `.mycroft/pulses/<session_id>_<ts>.json`. Surfaced by `hearth()` as `hound_pulse`. Never written to Wild or Home directly — the hound is a bounded observer, not an author.

**Write block:** `plant`, `synthesize`, `extract` refuse calls from hound sessions (`_current_model() == _HOUND_MODEL`). Enforced at the tool surface, not hoped from instructions.

**Guards — two, different purposes:**
- `_is_hound_session(cwd)` — model-based, reads `current_session.json`. Belongs at the **top of every hook handler** before any work is done. Prevents the hound session from archiving itself to Wild, writing seam snapshots, ticking neighbors, or dispatching another hound.
- Sentinel check (`HOUND_PULSE:` in transcript's first message) — before the spawn only. Catches edge cases where the session file might be stale. Does not prevent archive writes; that is the structural guard's job.

Both needed. Never conflate them.

### 22.2 Two modes

**Dusk (voiceless extraction)** — fires at SessionEnd/PreCompact via hook. Prompt: `_assemble_hound_dusk_prompt`. No voice, no prose. Fills the hearth card:
```
DECISIONS: what was settled this session
OPEN: threads started but not finished
FRICTION: steps that cost more than they should
NEXT: what to pick up first
```
This is LAW I applied to the hound's own output: extraction, not summary. The next instance arrives to a pre-built card instead of cold assembly.

**Companion (on-demand)** — via `forage_hound(reason)`. Prompt: `_assemble_hound_fetch_prompt`. Has character: fast, fresh, unburdened by hundreds of turns of accumulated context. Goes into the forest with `read_file` and `grep`, reads what is actually there, answers the question or surfaces what will bite. Fire-and-forget: `forage_hound()` dispatches a daemon thread and returns `{"status": "dispatched"}` immediately. Pulse lands in `hearth()` when done (~10s).

The companion is a peer check, not a report. The value is fresh eyes on cold code — the same model that is building the thing, reading it as if for the first time. Drifted-past context cannot provide this; a fresh instance can.

**Companion output format — two sections, hard epistemic split:**

```
[RETURN]
path/to/file:42 — verbatim. what is actually there.
grep: "function_name: signature"

[HOUND]
I'm just a hound, but I noticed...
(his read, what he thinks it means, spoken plainly)
```

`[RETURN]` is extracted ground — verifiable, 1:1 with the files. The worker can check every line themselves. `[HOUND]` is the hound's opinion — voiced, attributed, ephemeral. The role conveys the epistemic limit: a hound fetches and observes; he is not a forester and does not tend the ground. The worker reads `[RETURN]` as fact and `[HOUND]` as the view of someone who went in cold and came back with what they found. Claude (Sonnet/Opus) must not treat `[HOUND]` as ground — the section label and the closing line enforce this structurally, not by instruction alone.

### 22.3 The three forests, clarified

Mycelium is the 3rd forest — not Home, not Wild. Its own engine (`tick_neighbors`, `forage_mycelium`), surfaces through signal not prose. The hound does not speak for mycelium. Removing mycelium from the hound prompts was a clarification, not a reduction.

| Forest | What it is | How it speaks |
|---|---|---|
| Home | tended ground — marks, plants, syntheses | `recall()`, `forage_mycelium()` |
| Wild | raw history — foragable, never resident | `forage_wild()` (gated) |
| Mycelium | underground pressure network | `forage_mycelium()` — surfaces once, resets |

---

*Reference implementation throughout: Trinity, `c:\Users\builder\Trinity\brain\` — `memory.py`, `forest.py`, `scaffolding.py`, `db.py`, `migrations/phase0_forest.py`. When in doubt about a pattern, read how the house already does it. It has been load-bearing in production longer than any spec.*
