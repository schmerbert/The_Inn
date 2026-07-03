# .cabin — Technical State

*What exists, as of 2026-06-29. Present tense. The build spec is [IMPLEMENTATION.md](./IMPLEMENTATION.md); this document describes what is real.*

---

## Stack

- **Language:** Python 3.11+
- **Module:** `cabin/`
- **Data:** `.cabin/` per-project, `~/.cabin/` global shed
- **Embeddings:** `sentence-transformers` (`all-MiniLM-L6-v2`, 384-dim, on-device, lazy-loaded)
- **Vector index:** `sqlite-vec` (`vec0` virtual tables)
- **Storage:** SQLite — `.cabin/home.db` per-project, `~/.cabin/global.db` global
- **Transport:** FastMCP (`cabin` server, `mcp__cabin__*` tools)
- **No cloud. No API key required for memory.**

---

## Modules

```
cabin/
  db.py           — connection, init, bucket registry, schema migrations
  embed.py        — sentence-transformers wrapper, lazy-loaded, 384-dim
  filter.py       — extraction filter (strip scaffolding before archiving)
  forest.py       — _commit, writers, collector, archive_conversation, traverse
  hook.py         — lifecycle hook CLI (python -m cabin.hook <event>)
  hound_server.py — lightweight FastMCP for the hound: read_file + grep only
  instruments.py  — gauge, claim_check, seam_snapshot/diff, save_pulse, latest_pulse
  mycelium.py     — tick_neighbors, forage_mycelium, pressure
  scanner.py      — scan_repo, diff_scans (code forest / repo_map)
  server.py       — main FastMCP server, all 17 MCP tools
  cli.py          — thin terminal CLI for direct inspection
```

---

## Tests

**31/31 hostile commandments green** (`tests/test_hostile.py`). Named as commandments — the suite proves the laws hold under attack, not that the happy path works. Green means *refuses to break under attack*.

---

## What's live

### The laws in code

LAW I and LAW II enforced at `_commit` in `forest.py` — the single write chokepoint. One door. Validation sequence: bucket resolved → writer validated → forest crossing checked → voiced/voiceless rule checked → source-grip checked → embed → insert. Steps 1–6 reject before any side effect. No future writer can bypass.

`source_kind` is a closed vocabulary. Per-writer source requirements are validated at `_commit`, not hoped from callers.

### The three forests

**Home** — tended ground. Typed, named buckets; each independently switchable. Default buckets: `project` (voiceless, working memory), `personal` (voiced, authored keeps), `rationale` (voiced, decisions/synthesis), `conversations` (wild, raw archive), `repo_map` (voiceless, code forest).

**Wild** — raw history. Foragable, never resident. `forage_wild(query, reason)` requires a stated reason or returns the gate question. Nothing crosses to Home except through `synthesize()`.

**Mycelium** — underground pressure network. `tick_neighbors()` fires on PostToolUse (Write/Edit only — not searches, not prompts). `forage_mycelium()` returns the highest-pressure entry ≥ threshold as a verbatim excerpt; resets both counters on surface. Signal comes from the work, not the conversation around it.

### The hound

Bounded Haiku subprocess (`claude-haiku-4-5-20251001`). Attributed: model, session_id, timestamp, `HOUND_PULSE:` sentinel. Voiced and stored — legally, because signed. Not anonymous.

**Dusk mode** — fires synchronously at PreCompact. Fills the hearth card: DECISIONS / OPEN / FRICTION / NEXT. Voiceless extraction; no prose. Pulse written to `.cabin/pulses/`, surfaced by `hearth()` on next open. The next instance arrives to a pre-assembled card.

**Companion mode** — on-demand via `forage_hound(reason)`. Fire-and-forget (daemon thread); returns `{"status": "dispatched"}` immediately. Two-section output: `[RETURN]` (verbatim ground, verifiable) and `[HOUND]` (his read, attributed, humble). The epistemic split is structural — not enforced by instruction.

**Guards:** `_is_hound_session()` (model-based, top of every hook handler, blocks all side effects) + sentinel check (before spawn, blocks recursive spawning). Two guards, different failure modes; both required.

**`stdin=subprocess.DEVNULL` on all subprocess calls** — MCP servers communicate over stdio; inheriting the pipe causes a silent 90s hang.

### The breath cycle

- **Inhale:** `archive_conversation()` at PreCompact — conversation pairs extracted, filtered, written to Wild
- **Exhale:** hound dusk fires synchronously at PreCompact — pulse assembled before compaction begins
- **Arrive:** post-compact instance calls `hearth()`, sees pulse, reads seam — oriented, not assembling

Tested end-to-end and confirmed working in production.

### The hooks

| Event | What fires |
|---|---|
| SessionStart | One-line reminder to call `hearth()` (stdout → injected as context) |
| UserPromptSubmit | Gauge inject (stdout → before response) + session pointer persist |
| PostToolUse | file_changes.jsonl log + claim_check + tick_neighbors |
| PreCompact | archive_conversation → Wild + seam_snapshot + hound dusk spawn |
| Stop | seam_snapshot — skipped if no entries (preserves last good seam) |
| SessionEnd | archive_conversation + seam_snapshot + hound dusk spawn (fallback) |

### MCP tools

| Tool | What it does |
|---|---|
| `hearth()` | Orientation: project id, last seam, hound pulse, tool index |
| `recall(query, k?, buckets?)` | Forage Home |
| `forage_wild(query, reason)` | Forage Wild — reason-gated |
| `plant(body, source_content)` | Author a voiced, attributed keep in Home |
| `extract(bucket, source_id, span)` | Voiceless verbatim extraction into Home |
| `synthesize(wild_id, insight)` | Wild→Home crossing (LAW II gate) |
| `forage_mycelium()` | Surface highest-pressure entry; resets counters |
| `forage_hound(reason?)` | Dispatch companion hound (fire-and-forget) |
| `index_repo()` | Scan repo symbols, diff vs. prior layer, write new/changed to repo_map |
| `traverse(entry_id)` | Walk forest: session trail (±6 window) or source trail |
| `gauge()` | Context window fullness + trend + cache health |
| `claim_check(path, claim)` | Verify file contains assertion; flag drift |
| `seam_snapshot(entries)` | Freeze working set to timestamped file |
| `seam_diff(before, after)` | Diff two snapshots — what compaction silently dropped |
| `disable_bucket(bucket)` | Quarantine a polluted bucket (circuit-breaker, non-destructive) |
| `enable_bucket(bucket)` | Re-enable a quarantined bucket |
| `dismiss_pulse()` | Clear a stale hound pulse (renames .done, not deleted) |

### The code forest

`scan_repo(root)` — walks `.py` files, extracts module-level functions and class methods via `ast.iter_child_nodes` (nested functions excluded). Returns `{name, path, lineno, signature, docstring, body, source_hash}`.

`diff_scans(prev, curr)` — diffs by `source_hash`. Returns `{added, removed, changed, unchanged_count}`.

`index_repo()` — writes new/changed symbols to `repo_map` bucket. Old layers are pushed down, not overwritten. Newest layer always on top; opening inward walks backward in time. No stale data on top — a hostile commandment enforces this.

`traverse(entry_id)` — session trail uses `source_id = {session_id}:{line}`, returns the trailhead + ±6 window. Source trail returns the raw archive content a plant was grounded in.

---

## Known gaps

- **Gauge window denominator** — hardcoded at 200,000 tokens; real observed budget ~123-128k. The percentage is untrustworthy until pinned.
- **Seed lifecycle / planter** — designed (hound drops patterns into `planter` at dusk; tick builds pressure; at threshold, surfaced mid-work), not yet built.
- **Kill vs. cull** — distinction is made (kill = actively wrong, remove roots-and-all; cull = no thread emerged, let go), neither is implemented.
- **Mid-turn injection** — designed (PostToolUse surface signal when mark near current file crosses pressure threshold), not yet built.
- **Hearth restructure** — designed (three sections: HEARTH CARD / FILES IN FLIGHT / HOUND), not yet built.

---

## Roadmap (loose)

### Next: Panel (§21)
Browser/inspector for the forest state. The last structural piece. Write `PANEL.md` first — what to expose, when, what a human can reach for that doesn't cost the worker tokens — then build.

### After Panel
The parked design docs become the next phases:

- **`docs/TOKEN_COST_IDEAS.md`** — the economy layer. Aggressive token reduction; the best context is context that stayed outside the model until it was needed.
- **`docs/OBSERVABILITY.md`** — trust as a checkable thing. Build to arm defenders, not just to work.
- **`docs/LIFECYCLE.md`** — the scaling model: the shape, the marbles, the pouch.

These are design-first, build-second. None of them before Panel is done.
