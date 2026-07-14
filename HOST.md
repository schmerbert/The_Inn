# HOST.md — Layer 5 host contract

*Clinical register. Guests arrive through a host that owns the breath.*

**Read with:** ENTRY.md (posture) → this file (how to wake) → HANDOFF Cold worker map (doors).

## Why two skins

| Skin | Command / surface | Who owns wake |
|------|-------------------|---------------|
| **CLI (any OpenAI-compatible API)** | `python -m inn host` | Host **forces** inhale + pair-insert every turn |
| **MCP** | `python -m inn.mcp_server` | Guest must call `inhale`; same doors |

API CLI puts the guest **inside the machine**: orientation is a context return, not ambient IDE memory. MCP exposes the same doors to Cursor / Claude Code.

## First stay (5 minutes)

1. Copy `.env.example` → `.env` and set `INN_API_KEY` (gitignored).
2. Optional: `INN_API_BASE`, `INN_API_MODEL` (defaults = DeepSeek).
3. From repo root:

```powershell
python -m inn host
```

(`cli_host` loads `.env` automatically; existing env vars win.)

4. Talk about the manuscript; try Shelving only with your adopting words.
5. `quit` — host runs exhale seat check; if held, rewrite `HANDOFF.md` and retry `python -m inn breathe out`.

## Env (never commit secrets)

| Var | Required | Default | Meaning |
|-----|----------|---------|---------|
| `INN_API_KEY` | CLI yes | — | Bearer token |
| `INN_API_BASE` | no | `https://api.deepseek.com/v1` | OpenAI-compatible base URL (**include `/v1`**) |
| `INN_API_MODEL` | no | `deepseek-chat` | Model id |
| `INN_ROOT` | no | repo root | Marble path for multi-checkout |

## Wake contract (M4)

| Event | Call | Delivery |
|-------|------|----------|
| user message (CLI) | `inn.host.wake()` → `breath.inhale()` | packet JSON in context **once** per turn |
| user message (MCP) | tool `inhale` | same JSON shape |
| room change | `session.set_room` / tool `set_room` | next inhale reflects |
| message ingest | `inn.host.ingest_turn` (CLI auto) / tool `record_pair` (MCP) | real-time pair insert |
| end of stay | `breath.exhale()` — CLI on quit; MCP tool `exhale` | seat check; writer still rewrites HANDOFF |

**Packet fit discipline:** do not re-fit inhale mid-turn. One receipt per wake (`logs/breath/`).

## Guest-friction rules (Lake stay scars)

1. Blind wake refused — CLI always attaches a fresh inhale packet.
2. Packet is **homework**, not memory — cite ids/paths; do not invent bodies.
3. Ground only via `shelve` + author's adopting words — never `forest.adopt`, never silent file edit as authority.
4. Desk = model draft until Shelving.
5. Pair custody is host/tool duty — guest need not remember pair ids.
6. Warnings are filtered heuristics — drift is trustworthy; soft continuity is not.

## Known friction (honest)

| Friction | Status |
|----------|--------|
| Contradiction gauge on literary prose | Fast-filtered (188→0 on Lake); subtle continuity still weak |
| CRLF / trailing newline vs adoption hash | Normalized at shelve + compare |
| Manuscript author_direct has no adoption trail | By design; study Shelving carries diggable chain |
| MCP guest can skip `inhale` | Documented — IDE skins rely on guest discipline |
| Huge inhale JSON in context every CLI turn | Acceptable at L5; compress later if TTFT suffers |
| Exhale refuses until HANDOFF rewritten | Intentional (M5) |

## Tools exposed

| Tool | CLI | MCP | Crossing? |
|------|-----|-----|-----------|
| (auto wake) | every turn | call `inhale` | no |
| `read_ground` | tool | tool | **no** (lookup — opens manuscript/study ground text) |
| `shelve` | tool | tool | **yes** |
| `set_room` | tool | tool | no |
| `refuse_invention` | tool | tool | no |
| `record_pair` | auto after reply | tool | no |
| `exhale` | tool + on quit | tool | seat check |

## Latency / TTFT

| Stage | Source | Warn threshold |
|-------|--------|----------------|
| inhale fit | envelope `fit_ms` / ledger `timings_ms.total` | > 500ms (CLI prints warn) |
| model | envelope `model_ms` | document only |
| crossings | Shelving | deliberate — never rush |

Envelope logs: `logs/host/*-turn.json` (ids/timings only).
Full prose: `logs/host/*-stay.md` (one file per CLI stay; printed at start/quit).

## MCP (Cursor / Claude Code)

```json
{
  "mcpServers": {
    "the-inn": {
      "command": "python",
      "args": ["-m", "inn.mcp_server"],
      "cwd": "D:/AI/TheInn"
    }
  }
}
```

On session start: **call `inhale` first**. Do not invent ground. Use `shelve` only with the writer's adopting words. Call `record_pair` after substantive turns (CLI does this for you).

## Parity

Automation must match [`BREATH.md`](BREATH.md) M1–M2 semantics (M3–M5 here). Tests mock HTTP — no live API in CI.
