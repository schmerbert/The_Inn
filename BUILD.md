# BUILD.md — layer tracker

*Living document. Rewritten at the end of each build layer.*
*Stable reference: BUILD_SPEC.md (pass 2). Ancestry notes are marked below.*

---

## Current layer: **3 — Ground** (complete)

| Layer | Status | Commit |
|-------|--------|--------|
| 0 — Map | complete | first commit (map, zero construction) |
| 0.5 — Spec hardening | complete | BUILD_SPEC, AGENTS, rooms+breath architecture |
| 1 — Bones | complete | rooms registry, schema, stubs, hostile floor |
| 2 — Gates | complete | `shelve.py` write path; tests 1–3 green |
| **3 — Ground** | **complete** | breath ground fitting; test 5 inhale green |
| **4 — Breath** | **next** | pair insert, traverse, `BREATH.md`, breath ledger + inhale timings |
| 4.5 — Responsiveness | pending | diegetic latency, packet receipts, lookup vs crossing SLOs |
| 5 — Host | pending | wake coupling, TTFT/streaming gates, tool timeouts |
| 6 — Skin | pending | — |

---

## Layer 3 deliverables

- [x] `breath.inhale` — M0.5 assisted ground fitting (layer 3)
- [x] `compare.scan_ground_warnings` — drawer drift + contradiction gauge
- [x] Adoption chain (`cites` edge + `adoption_record_ids` in ground slot)
- [x] `source_verbatim` trailhead — required manuscript, optional study
- [x] `tests/hostile/test_contradiction.py`
- [x] `shelve` records `meta_json.ground_path` on adoption_record
- [x] `ROOM_READ_BUCKETS` in `breath.py` (BUILD_SPEC join table)
- [x] Hostile test 5 inhale integration green
- [x] `tests/positive/test_ground_fitting.py`
- [x] `tests/positive/test_cold_wake.py` — `python -m inn breathe` without prior init

**Test state:** `python -m pytest tests/hostile tests/positive -q` → **17 passed**

**Next layer:** 4 — Breath (core + observability floor). See deliverables below.

**After layer 4 (owner):** first real stay — live testing + friction fixing with
writer prose (short story excerpt); M2 reference session archived. See HANDOFF
§ After layer 4. API key and daily-driver inhabitability are **layer 5 Host**,
not layer 4.

**Polish roadmap:** BUILD_SPEC § Responsiveness + § AI optimization checklist.
Layer 4 lays the **observability floor**; 4.5 makes latency **designed**; 5 makes
it **measurable** (TTFT, streaming). Do not skip 4 for 4.5 — manual breath is
the parity spec automation must pass.

---

## Layer 4 deliverables (next)

*Trust path first. Observability stubs here so 4.5/5 inherit traces, not tar notes.*

### Core (M1–M2 manual breath)

- [ ] `forest.insert_pair` — real-time pair insert at message ingest (woods custody)
- [ ] Manual traverse by proximity from `last_pair_root_id` — document in `BREATH.md`
- [ ] `BREATH.md` — M1 inhale script + M2 exhale script (BUILD_SPEC ladder)
- [ ] Reference session script in `BREATH.md` — owner M2 walkthrough checklist
- [ ] `tests/positive/test_pair_insert.py` — pair lands in woods with signature

### Observability floor (pave for 4.5 — build with layer 4, not after)

- [x] `inn/breath_ledger.py` — append-only receipt writer (`logs/breath/`) *(stub landed 2026-07-08)*
- [x] `logs/breath/README.md` — one line: slot → id/path map per wake; not prose
- [ ] `inhale()` stage timings — ms per slot (`warnings`, `ground`, `pressure`, total)
- [ ] Receipt per wake — log slot ids filled; same shape manual M1 step 8 would write
- [ ] `tests/positive/test_breath_ledger.py` — wake writes one receipt; cites ids only
- [ ] `tests/positive/test_inhale_deterministic.py` — same woods + session → same packet

**Pick at layer 4:** `logs/breath/` append-only (no schema migration). Automation
at layer 5 must produce receipts a human would have written in M1.

**Test state target:** prior 17 green + new positive tests above.

---

## Layer 4.5 deliverables — Responsiveness

*Diegetic latency + packet discipline. No host, no model loop — design and prove
the floor before TTFT exists. Checklist: BUILD_SPEC § AI optimization checklist.*

| Checklist row | 4.5 deliverable | File / test |
|---------------|-----------------|-------------|
| Packet fit discipline | one `inhale()` receipt per wake; no hidden re-fit mid-turn | `breath_ledger.py`; `test_breath_ledger.py` |
| Crossing vs lookup separation | two SLO classes documented; crossings stay deliberate | `BREATH.md` § Latency classes |
| Observability | stage timing envelope on every wake | `inhale()` timings → ledger JSON |
| TTFT / first breath | **inhale-only budget** — p50/p95 `fit_packet` ms (not model TTFT yet) | `BREATH.md` § Inhale budget; ledger fields |
| Prompt/context budget | injection grammar + ≤1 unsolicited surfacing; focusing zero | `BREATH.md` § Surfacing rules |
| Deterministic refusal | existing hostile suite stays green; document lookup vs crossing | no new pytest — manual reference session |
| Streaming / tool reliability | **deferred to layer 5** — document thresholds only | `BUILD.md` layer 5 preview |

### Deliverables

- [ ] `BREATH.md` § **Diegetic latency** — nod / drawer / meal / Shelving table (BUILD_SPEC)
- [ ] `BREATH.md` § **Latency classes** — lookup (fast, metaphor) vs crossing (deliberate, gate)
- [ ] `BREATH.md` § **Inhale budget** — fail threshold for `fit_packet` p95 (e.g. warn >500ms)
- [ ] `BREATH.md` § **Surfacing rules** — ≤1 unsolicited; focusing closed = zero
- [ ] `hearth.json` workflow — writer fills `standing_context`; inhale slot already wired
- [ ] Manual reference session — log diegetic beats + stage timings; archive to `logs/`
- [ ] `tests/positive/test_inhale_receipt.py` — receipt lists every non-empty slot by id/path
- [ ] HANDOFF + Cold worker map — `breath_ledger` row live

**Inhabitable posture after 4.5:** intentional — writer feels *designed* slowness at
gates, fast nod at lookups; traces exist when something feels wrong.

**Not in 4.5:** speculative retrieval, rerankers, embeddings, visitors subprocess,
model routing — layer 6+ (checklist nice-to-have table).

---

## Layer 5 deliverables preview — Host + measurable polish

*Name now; build after M2 manual breath is boring. Checklist rows that need a host:*

| Checklist row | Layer 5 deliverable | Gate |
|---------------|---------------------|------|
| TTFT / first breath | wake → first model token p50/p95 | fail threshold in `HOST.md` or BUILD_SPEC amend |
| Streaming quality | stream starts early; chunk cadence logged | no end-only render in host logs |
| Tool reliability | bounded retries, explicit timeouts | p95/p99 + timeout receipts per tool |
| Prompt/context budget | stable prefix cache-hit metric | log cache read vs write per turn |
| Packet fit discipline | M3 parity — `inhale()` matches M1 ledger | `tests/positive/test_breath_parity.py` |
| Wake coupling | host calls `inhale()` on message; tool return | same JSON as M3 |
| M4–M6 breath ladder | assisted inhale, exhale seat check, hooks | BUILD_SPEC manual ladder |

- [ ] `HOST.md` (or BUILD_SPEC amend) — host contract table + TTFT/streaming SLOs
- [ ] `inn/breath.exhale()` — seat check; stale HANDOFF refused
- [ ] Session capture hooks — pair insert on message ingest
- [ ] Per-turn timing envelope — fit / retrieve / model / emit in host logs
- [ ] Nice-to-have **deferred to 6+:** speculative retrieval, routing, prefetch, compression

---

## Layer 2 deliverables (complete)

- [x] `shelve.py` write path — ground file + `adoption_record` (`body_hash` + `content_hash`)
- [x] `permissions.ground_file` in study + manuscript `room.yaml`
- [x] Hostile tests 1–3 green (refusal + happy path)
- [x] `tests/positive/test_shelve_happy.py` — full adoption trail

---

## Notes for next builder

- **Read order:** BUILD_SPEC § Responsiveness + § AI optimization checklist → this file § Layer 4–5 → `INHALE_PACKET` in `breath.py`.
- **Inhale** = `fit_packet`; `init_db` on every wake (idempotent). Cites ids/paths only.
- **Breath ledger** (layer 4) = `inn/breath_ledger.py` → `logs/breath/`; one receipt per wake.
- **Compare** = `scan_ground_warnings` (drift + contradictions); `check_drawer` for one drawer
- **Shelving** = `inn/shelve.py` only — one crossing; `ground_path` in adoption meta.
- **Ground file** = `room.yaml` → `permissions.ground_file`; no hardcoded room paths in Python.
- **Contradiction scan** live in `compare.scan_ground_warnings` (within-room, cross-room, superseded-in-file).
- **Cold worker map** in HANDOFF.md — module → door → returns.
- **Seams closed:** `session.yaml`, room↔bucket table, dual hash (`body_hash` + `content_hash`).
- **Schema authority:** `woods/schema.sql` here — FOREST.md is lineage only.
- **Polish bar:** if a stay feels like slop, name the failed checklist row + require trace from ledger/host logs — not vibes.
- Last real use: still none. **Post–layer 4:** owner runs first real stay (HANDOFF § After layer 4).
- Hostile tests 4 and 6 remain manual/eval — not built.
- **API key:** layer 5 Host only; layer 4 = CLI + manual breath, no model loop required.

---

## Ancestry marker

Layer 0.5–2 notes preserved in git history and BUILD_SPEC/HANDOFF.

---

*Updated: 2026-07-08 — layer 4/4.5/5 paved roadmap (responsiveness checklist → deliverables).*
