# BREATH.md — manual breath ladder (layer 4 reference + 4.5 floor)

This file is the manual parity spec for breath growth.
Automation in layer 5+ must match this procedure, not replace it semantically.

## M1 — manual inhale

1. Read `.inn/session.yaml` (`current_room`, `proximity`, `files_in_flight`).
2. Read `rooms.yaml` + current `<room>/room.yaml` posture/permissions.
3. Read `hearth.json` (`standing_context`).
4. Run compare warnings on ground rooms (drift + contradiction warnings).
5. List relevant ground adoption ids/paths from proximity.
6. List open questions (`question` bucket) near proximity, traversing from
   `last_pair_root_id` when present.
7. Copy seam fields (`files_in_flight`, `last_pair_root_id`).
8. Write a receipt in `logs/breath/` (slot ids/counts only; no prose).

Or: `python -m inn breathe` (M0.5 assisted fitting + receipt).

## M2 — manual exhale

1. Ensure new session messages are inserted in woods custody.
2. Run seat freshness check before rewriting `HANDOFF.md`.
3. Rewrite HANDOFF texture citing ids/paths (no body copy).
4. Update seam in `.inn/session.yaml`.
5. Write exhale receipt in `logs/breath/` (trailhead; layer 5 implementation).

## Reference session checklist (owner M2 — *The Lake* 2026-07-13)

Use writer prose on `manuscript/` (author_direct). Clinical fixtures stay in `tests/`.

1. [x] Land excerpt on `manuscript/ground.md`
2. [x] `python -m inn breathe` — warnings/ground/pressure + receipt
3. [x] Shelve study railing with adopting words (date auto-stamped)
4. [x] Tamper drawer → inhale drift warning → restore
5. [x] Hostile live: praise refuse / paraphrase refuse / invention → question
6. [x] Weather re-shelve (adoption chain `cites`)
7. [x] Contradiction gauge usable on literary prose (fast filters)
8. [x] Archive stay to `logs/` (`08-2026-07-13-lake-m2-reference-stay.md`)
9. [x] Rewrite HANDOFF Cold worker map (captured_at + filtered compare)

**Stay scars (do not rediscover):**

- Shared-vocab “contradiction” flooded inhale (~188) until filters
- CRLF / trailing newline tripped drift falsely — normalize at hash
- Manuscript author_direct has no adoption trail; study does
- Dates belong on capture (`meta.captured_at`), not typed by writer
- Warm “implied promotions” = attention only; never soft-canon (defer)

## Diegetic latency (layer 4.5)

| Latency | In-world | Clinical |
|---------|----------|----------|
| <300ms | silent nod | no announcement |
| 300ms–2s | one-drawer check | single traverse / compare |
| 2s+ | "let me check…" / meal | staged context bundle |
| deliberate | Shelving read-back | authority gate — never rush |

Arrival inhale is **immediate** (clinical packet). Diegetic latency is for
**mid-session retrieval**, not fake delay at the door.

## Latency classes

| Class | Examples | SLO posture |
|-------|----------|-------------|
| **Lookup** | inhale fit, drawer hash check, list rooms | fast; borrow metaphor (nod) |
| **Crossing** | `shelve()`, burial (later) | deliberate; human-paced |

Do not make crossings “fast” by skipping read-back. Do not make lookups feel
like loading a database.

## Inhale budget

From ledger `timings_ms.total` (and per-slot):

| Signal | Threshold |
|--------|-----------|
| comfort | p50 fit ≲ 100ms on local SSD |
| warn | any wake `total` **> 500ms** |
| fail (host later) | p95 fit sustained > 500ms without cause |

Receipts already record stage ms. Layer 5 hosts enforce; layer 4.5 documents.

## Surfacing rules

- ≤1 unsolicited mid-session surfacing per turn unless writer asks
- Focusing closed = **zero** surfacing (not quieter)
- Surface as looking / plate / note — never “querying db”
- Injection grammar (nod < gesture < meal < note): PREBUILD ancestry

## Notes

- `inn.breath.inhale()` = deterministic M0.5 fitting + ledger receipt
- `inn.breath_ledger` → `logs/breath/` (JSON gitignored; README kept)
- **M3–M4 (layer 5):** `python -m inn host` / MCP `inhale` replace manual packet fill;
  same JSON homework shape — see `HOST.md`
- **M5:** CLI quit + `python -m inn breathe out` / tool `exhale` — seat check;
  writer rewrites HANDOFF if held
- **M6 (partial):** inhale may include `pulse` (faun gesture) — consumed on fit;
  dies after one wake. Plant via host quit or `python -m inn pulse`.
  Hearthstone path in packet when `assets/hearth/hearth.jpg` present.
- Host turn envelopes → `logs/host/` (gitignored JSON); stay transcripts `*-stay.md`
- Warm candidates / mycelium / visitors / wander → still deferred
