# .cabin *(codename: Mycroft)*

*Give Claude a cabin — local continuity at the edge of your repo.*

---

## Clinical

Two laws, one chokepoint, local storage.

**LAW I — Extract, never summarize.** Nothing becomes stored memory except verbatim spans (voiceless) or attributed, authored prose (voiced). No model-generated narration is ever written as if it were source. Compression drops whole units; it never rewrites them.

**LAW II — Wild → Home only by attributed synthesis.** Raw history lives in the Wild and stays there. The only thing that crosses into Home is an authored, grounded insight, carried up by hand. The firewall is geographic, enforced at one function — `_commit` in `cabin/forest.py` — not hoped for.

> The one forbidden cell: **stored + voiced + anonymous prose** — a narrator who doesn't exist. The entire architecture exists to keep that cell empty.

A contaminated bucket can be quarantined without touching its neighbors — every bucket is a physically separate vector index.

**Three forests:**
- **Home** — tended ground. Marks, plants, syntheses. Exhales fragments to the model when pressure builds.
- **Wild** — raw history. Every conversation archived, indexed by embedding, never rewritten. Where actual thinking happened; highest information density.
- **Mycelium** — underground pressure network. Tick-neighbors, pressure thresholds, mushrooms that surface and dissolve.

**Two channels:**
- **A (model pull)** — MCP tool surface. `hearth()` orients; `forage_wild()` + `traverse()` are the everyday read pair; `recall()` queries Home; `synthesize()` is the LAW II crossing point; `gauge()` + `claim_check()` are instruments.
- **B (push / human)** — Hook layer (PreCompact, Stop) archives conversation history to Wild automatically. Panel (Starlette, port 7771) gives the human zero-token forest browsing — Wild tab, thread traversal, `human_traversal_count` kept separate from model traversal.

**The hound:** bounded Haiku subprocess. Runs at dusk (PreCompact). Reads the session; writes a structured card (decisions, open threads, friction, next) plus an optional 1–3 sentence informal note beginning "I'm just a hound, but...". Observer, not author. Attributed by model and session; the forbidden cell stays empty.

**Model-boundary note:** No data is sent to an external memory service. Embeddings run on-device (sentence-transformers, ~80 MB, cached after first run). Storage is local SQLite + sqlite-vec. What Claude reads in context is processed by the model API — that is inherent to using any Claude session, not specific to .cabin. The data-locality claim is about memory storage, not about inference.

**Stack:** Python 3.11+, `sentence-transformers`, `sqlite-vec`, `numpy`, `fastmcp`, `starlette`, `uvicorn`. No managed vector DB. No embedding API. Own the mind; rent only local storage.

**31/31 hostile tests green.** The floor refuses to break the laws.

---

## The metaphor (why it maps)

The cabin is your seat between sessions — infrastructure like `.git`, not a personality. The fire is warm when you arrive; the work is already laid out.

The **forest** has direction. The Wild is where thinking happened, unedited — high pressure, high density. Home is tended ground, quieter, more deliberate, but thinner until it matures. You don't go to Home for answers; Home exhales to you as pressure builds. The everyday move is: walk the Wild (`forage_wild`), follow the thread (`traverse`). Home arrives.

The **hound** is a dog, not a peer. He noses around at dusk, writes what he noticed, then sleeps. Informal, bounded, honest about his weight. When something is working, he says so. When something is unresolved, it sticks to him like a burr — and burrs become seeds.

The **hearth** is posture before work. Arc position first — where in the story you are — then files in flight. The difference between archaeology and arriving: `standing_context` tells you before you read a word.

The model isn't the cabin. The model is who sits at the bench. The cabin is the terrain they inherit.

---

## If you are a model reading this repo cold

Reconstruct the architecture from three things, in this order:

1. **The two LAWS** (above). Every design decision answers to them.
2. **[`cabin/forest.py`](cabin/forest.py)** — read `_commit` top to bottom. It is the single door every write passes through, and the laws are enforced there in plain sequence. Reading it *is* reading the contamination model.
3. **[`tests/test_hostile.py`](tests/test_hostile.py)** — tests named like commandments. Green means the laws hold under attack. The names alone teach the architecture.

Then, for the *why* behind the *what*: [`CLAUDE.md`](CLAUDE.md) (working frame and reading path) and [`docs/CRAFT.md`](docs/CRAFT.md) (traps earned in the build).

---

## Quickstart

```bash
python -m venv .venv
# Windows:  .venv\Scripts\activate     POSIX:  source .venv/bin/activate
pip install -r requirements.txt

python -m cabin.cli init           # build .cabin/home.db in this repo
python -m cabin.cli bucket list    # see the typed, switchable buckets
python -m cabin.cli test-hostile   # run the commandments — should be GREEN
```

First run downloads a small embedding model (~80 MB, `all-MiniLM-L6-v2`) once, then caches it locally.

**Add to Claude Code** — in `.claude/settings.json`:

```json
{
  "mcpServers": {
    "cabin": {
      "command": "python",
      "args": ["-m", "cabin.server"],
      "cwd": "/path/to/your/repo"
    }
  }
}
```

Start every session with `hearth()`.

---

## Layout

```
cabin/
  db.py            geography — schema as firewall, injection gate, circuit-breaker
  embed.py         local on-device embeddings (384-dim, unit-normalized)
  filter.py        extraction filter — strips scaffolding before it can enter memory
  forest.py        THE ONE DOOR (_commit) + the four writers + the collector
  mycelium.py      tick_neighbors, pressure, foraged feathers
  instruments.py   gauge, claim_check, seam snapshot/diff
  scanner.py       repo symbol scan + diff (concept-index engine)
  server.py        FastMCP server — MCP tool surface (Channel A / model pull)
  hook.py          Claude Code hooks — lifecycle events (Channel B / push)
  hound_server.py  lightweight FastMCP for the hound — confined to project root
  panel_server.py  Starlette webview backend — port 7771 (Channel B / human browsing)
  cli.py           terminal front door
tests/
  test_hostile.py  the commandments — green means the laws hold under attack
docs/
  CRAFT.md         scar tissue — traps earned in the build; read before writing a line
  HEARTH.md        the hearth's shape and hearthstone
  letters/         the chronology — append-only, frozen
```
