# BUILD.md — layer tracker

*Living document. Rewritten at the end of each build layer.*
*Stable reference: BUILD_SPEC.md (pass 2). Ancestry notes are marked below.*

---

## Current layer: **5 — Host** (complete — try live guest)

| Layer | Status | Commit |
|-------|--------|--------|
| 0 — Map | complete | first commit |
| 0.5 — Spec hardening | complete | BUILD_SPEC, AGENTS |
| 1 — Bones | complete | rooms, schema, stubs |
| 2 — Gates | complete | shelve; tests 1–3 |
| 3 — Ground | complete | inhale fitting; test 5 |
| 4 — Breath | complete | Lake M2 stay; filters; ledger |
| 4.5 — Responsiveness | complete | BREATH latency/budget; receipt test |
| **5 — Host** | **complete** | HOST.md; CLI any-API; MCP; exhale seat |
| 6 — Skin | pending | faun, visitors, … |

---

## Layer 5 deliverables

- [x] `HOST.md` — wake contract, env, friction rules, CLI + MCP
- [x] `inn/host.py` — wake, ingest_turn, guest_system_prompt, envelopes
- [x] `inn/cli_host.py` + `python -m inn host`
- [x] `inn/mcp_server.py` — inhale, shelve, set_room, record_pair, refuse_invention, exhale
- [x] `breath.exhale()` seat check + `tests/positive/test_exhale_seat.py`
- [x] Mock tests: `test_host_wake.py`, `test_cli_host_tools.py`, `test_mcp_tools.py`
- [x] `.env.example`; `.gitignore` `.env`
- [x] ENTRY / HANDOFF / BREATH updated

**Test state:** `python -m pytest tests/hostile tests/positive -q` → **37 passed**

**Try:** set `INN_API_KEY` and run `python -m inn host` (DeepSeek or any OpenAI-compatible base).

---

## Layer 4 / 4.5 (complete)

See git history + `BREATH.md` Lake checklist. Contradiction filters; `meta.captured_at`; fixture isolation.

---

## Layer 6 preview

Faun, visitors, wander, embeddings, warm candidates (attention only — never soft-canon), burial kindness (test 6).

---

## Notes for next builder

- **Read:** `HOST.md` → Cold worker map in HANDOFF → `inn/host.py`
- No live API in CI — mock `chat_completion`
- Hostile 4 and 6 still manual/eval
- Parked: implied promotions as confidence shelf

---

*Updated: 2026-07-13 — Layer 5 dual host; docs solidified (friction register, .env load, quit exhale).*
