# PANEL.md — The human's second window

*The first window is Claude's gauge injection — the cabin pushing context signals into the conversation. This is the second window: the cabin talking directly to the human, bypassing Claude's context entirely, at zero token cost.*

---

## What it is

A VS Code panel (sidebar webview) — the human's direct channel to what the cabin knows and what is happening right now. Two doors into the same cabin: the MCP server is Claude's door (Channel A, pull); the panel is the human's door (Channel B, push — the cabin surfaces to you without being asked).

**What it is not:** a config UI, a chat interface, a log viewer. It is a live signal surface and a memory instrument.

**The distinction that shapes the whole design:** there are two groups of things the panel does.

*Live channel* — the cabin talking to the human:
- Context pressure, trend, thrashing state — visible before Claude knows to warn
- Hound pulse — DECISIONS / OPEN / FRICTION / NEXT — the cabin's last word to itself
- Pressure neighbors near threshold — what the mycelium is about to surface to Claude
- Seam losses — what the last compaction dropped

*Research instrument* — the human using the cabin:
- Forest browser — "Ask the forest" at zero tokens while Claude is mid-sentence
- Memory state — bucket list, entry counts, quarantine control
- Seam history — the audit trail, diffable
- Hound dispatch — send the hound without interrupting Claude

Build and design the live channel first. The moment the gauge bar updates while Claude is working, the user understands immediately what the panel is.

---

## The constraint that shapes everything

**The panel cannot go through Claude's context.** Zero tokens. The human queries the forest while Claude is mid-session, working on something else, spending none of his budget.

This rules out MCP for the panel's read path. The panel reads from the DB directly, via a lightweight local panel server (separate process, separate port from the MCP server). The VS Code extension starts the panel server when the workspace opens.

```
Claude Code  →  MCP server (port A)  →  cabin core
Panel        →  panel server (port B)  →  cabin core  (same DB, same buckets)
```

WAL mode is already set in `db.connect()` — a reader can run while the MCP server writes. This is structural, not coordinated.

---

## The data provenance principle

**Every data point shown in the panel carries its full lifecycle label.**

Data in the cabin is like a forest animal: it is born somewhere, lands in a place, moves through the forest, accumulates pressure, surfaces when conditions are right, and can be dismissed or have its territory quarantined. The panel makes every stage of that journey visible.

At minimum, every entry rendered anywhere in the panel shows:

| Label | Field | What it means |
|---|---|---|
| **Origin** | `source_kind` + `writer` | Where did this come from? (`extract`, `plant`, `synthesize`, `archive`) |
| **Author** | `author` + `model` | Who wrote it and which model? |
| **Forest** | `forest` (home/wild) + `bucket` | Where does it live? |
| **Voice** | `voiced` (from registry) | Authored prose or verbatim extraction? |
| **Born** | `created_at` | When did it land? |
| **Traversed** | `traversal_count` + `traversed_at` | Has it been recalled? When last? |
| **Pressure** | `neighbor_pressure` + `surface_pressure` | How close to surfacing? |
| **State** | `dismissed` | Has it been screened out this session? |

Do not collapse these. An entry without its provenance trail is data without a chain of custody — exactly what the laws exist to prevent. The panel rendering must be as honest as the DB schema.

---

## The views

### Group 1 — Live channel (build first)

#### 1a. Hearth card — always visible, top of panel

What Claude sees on arrival, live and updating:

- **Project** — name, db path
- **Gauge bar** — visual bar, color-coded: green / yellow / red. Updates on a slow poll (3-5s) while Claude works. The human watches context pressure climb in real time and can act before Claude knows to warn.
- **Trend state** — steady / climbing / converging / thrashing. Thrashing should look alarming. This is the signal that reaches the human before Claude can name it.
- **Hound pulse** — last dusk extraction: DECISIONS / OPEN / FRICTION / NEXT. Rendered with full provenance: which session, which model ran the hound, when.
- **Last seam** — timestamp + files in flight at that moment.

#### 1b. Live notifications — the cabin speaking

A live surface. The forest pushes signals here that are too low-confidence or too noisy to route through Claude's context — but exactly right for a human who can glance and act in two seconds.

**What surfaces here:**

- **Pressure neighbors near threshold** — entries where `neighbor_pressure + 2 * surface_pressure >= PRESSURE_THRESHOLD` (currently 3). The human sees what the mycelium is about to say to Claude. Dismiss before it costs tokens, or let it through.
- **Seam losses** — diff of the two latest `.cabin/seam/*.json` snapshots. Files that were in flight before compaction and are now gone. "These files dropped off the seam at last compact." The human decides what to inject back.
- **Hound pulse arrivals** — when a new pulse lands (dusk or mid-session dispatch), surface it here as well as in the hearth card.

Each notification has two actions: **Dismiss** (ignore for this session, sets `dismissed=1` on the entry) and **Bring to Claude** (flag for injection into the next message). The human is a smarter router than any heuristic.

**What is not surfaced here (not built):**
- Dropped threads detected from conversation text — requires per-turn NLP, not implemented.
- Cross-session debt patterns — requires session mention tracking, not implemented.

### Group 2 — Research instrument (build second)

#### 2a. Forest browser — the wow moment

A query field. The human types anything — a question, a term, a half-formed thought. The forest surfaces what it knows. Results render below with **full provenance labeling** per the data provenance principle above.

**This is zero tokens.** Claude doesn't know this happened.

Design notes:
- Label it: **Ask the forest**
- Results feel found, not queried — foraging, not search
- Filter rail: Home / Wild / bucket selector / voiced only / dismissed toggle
- Pressure indicator per entry — entries near threshold feel different from cold ones
- Distance score shown — how close is this to your query?

#### 2b. Memory state — buckets and pressure

All registered buckets, both project-scoped and global (the shed). For each:

- **Name** — bucket slug
- **Forest** — home or wild
- **Voiced** — yes or no
- **Entry count** — how full is this bucket?
- **Enabled state** — live or quarantined
- **High-pressure entries** — entries near or at feather threshold (`neighbor_pressure + 2*surface_pressure >= PRESSURE_THRESHOLD`), listed inline
- **Quarantine button** — one click sets `enabled=0`. The circuit-breaker. Should feel consequential.

Default buckets that will appear (project scope: project, personal, rationale, conversations; global shed: craft, seedbank).

#### 2c. Seam history — the invisible made visible

A list of seam snapshots from `.cabin/seam/`. Each entry:

- Timestamp
- Files in flight at that moment
- **Diff button** — compares this snapshot against the previous one: which files were added, which dropped off. The dropped list is the audit: were those files' changes captured in the compaction summary, or silently lost?

This is where the transparency pitch becomes real. No other tool shows what compaction actually preserved.

#### 2d. Hound dispatch

A **Send the hound** button. Optional reason field. Fires the hound subprocess directly (same machinery as `SessionEnd`) without going through a Claude tool call — useful when the human sees something in the forest browser and wants a second opinion without interrupting Claude mid-thought.

Pulse lands in the hearth card and live notifications when done.

---

## Architecture

```
cabin/panel_server.py      — lightweight HTTP (FastAPI), separate port from MCP server
  GET /state               — hearth card data: project, gauge, seam, pulse
  POST /forage             — embed query, k-NN home buckets, return hits (zero-token browse)
  GET /buckets             — bucket list with entry counts, enabled state, pressure entries
  POST /quarantine/:b      — disable_bucket (sets enabled=0)
  POST /dismiss/:id        — set dismissed=1 on an entry
  GET /seam                — list seam snapshots from .cabin/seam/
  GET /seam/diff           — diff two snapshots
  POST /hound              — dispatch hound subprocess
  GET /notifications       — live: pressure neighbors, seam losses, new pulses
  POST /notify/dismiss     — dismiss a notification for this session

.vscode-extension/         — VS Code extension (TypeScript)
  panel webview            — HTML/CSS/JS, calls panel_server over localhost
  starts panel_server      — on workspace open, via child_process
  WebSocket or polling     — gauge and notifications update live (3-5s poll)
```

**DB access:** the panel server imports `cabin.db` and `cabin.embed` directly. Same `.cabin/home.db` the MCP server uses. One DB, two doors, no shared state beyond the file. WAL mode makes concurrent reads safe.

**Embedding in the panel server:** the forest browser embeds the user's query using `cabin.embed` directly — not through Claude, not through MCP. Zero-token foraging is structural.

**Gauge:** the panel server reads `.cabin/current_session.json` (written by the hook on every UserPromptSubmit) to find the live transcript path, then calls `instruments.gauge()` directly.

---

## Design constraints

**1. The panel is read-only to the core loop.**

The self-feeding cycle — archive → pressure → feathers → Claude → archive — runs completely without the panel. Closing it changes nothing. The panel's only writes are tuning signals: `dismissed=1`, `enabled=0`, hound dispatch. These improve signal quality; they don't drive the loop.

Rule: ignore the panel → lose nothing. Use it → gain signal quality and human visibility. No feature may make itself load-bearing to the core loop.

**2. Every data point carries its provenance.**

See the data provenance principle above. Do not surface an entry without its lifecycle labels. An entry without a chain of custody is noise pretending to be signal.

**3. The hound is the mycelium's future.**

`tick_neighbors` is the current mechanical pressure accumulator — cheap, always-on, cosine-gated. The hound (dusk pass) is the smarter layer above it. Don't build toward this now. Build `tick_neighbors` + `forage_mycelium()` as designed; note this direction so nothing in the panel closes the door on it.

---

## The wow moments — design around these

**1. The gauge updates while Claude works.** The human watches context pressure climb in real time. They know a compact is coming before Claude does.

**2. Trend goes "thrashing."** The gauge bar turns red and the trend label reads THRASHING. The human can redirect Claude — "you're going in circles, here's the pointer" — before Claude has spent another three turns digging.

**3. "Ask the forest" while Claude is mid-sentence.** The human types a question. Results surface, provenance-labeled. Claude never knew. This is the thing that changes what the panel *is* — not a status display but a parallel instrument.

**4. The seam diff.** The human opens the last compaction and sees which files dropped off. The invisible made visible. Trust is not assumed — it is checkable.

**5. A pressure neighbor surfaces in the panel before Claude sees it.** The human decides: let it through, or dismiss it here. Agency before the moment.

**6. Quarantine in one click.** Something wrong in a bucket. One button. The system adapts.

---

## Build order

1. **Panel server** — `cabin/panel_server.py`: `/state`, `/forage`, `/buckets`. Read paths first; no writes yet. Prove zero-token foraging and live gauge work.
2. **VS Code extension scaffold** — bare webview, connects to panel server, renders `/state`. Gauge bar visible and live. This is the proof of concept for the whole channel.
3. **Live notifications** — `/notifications` + the notification surface. Pressure neighbors, seam losses. Dismiss action.
4. **Forest browser** — the query field + results with full provenance labeling.
5. **Quarantine + dismiss** — the write paths. One button each.
6. **Seam history** — the diff view. Requires real compaction data to be meaningful.
7. **Hound dispatch** — button in panel. Wires to the existing subprocess machinery.

---

## What not to build

- No chat interface. The panel surfaces and controls; it does not converse.
- No auto-refresh on every keypress. Gauge polls at 3-5s; forest browser is on-demand only.
- No write path for forest entries from the panel. Memory authoring stays with Claude (`plant`, `synthesize`). The human's hands are quarantine and dismiss — immune system controls, not authoring controls.
- No markdown rendering of entry bodies in the browser results. Verbatim is the point. Don't dress it up.
- No dropped-threads detector or cross-session debt tracker. Not built; don't stub them in as placeholders.
