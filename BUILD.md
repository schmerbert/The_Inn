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
| **4 — Breath** | **next** | pair insert, traverse by hand, `BREATH.md` |
| 4.5 — Responsiveness | pending | — |
| 5 — Host | pending | — |
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

**Next layer:** 4 — Breath. Pair insert in real time, manual traverse, `BREATH.md`.

---

## Layer 2 deliverables (complete)

- [x] `shelve.py` write path — ground file + `adoption_record` (`body_hash` + `content_hash`)
- [x] `permissions.ground_file` in study + manuscript `room.yaml`
- [x] Hostile tests 1–3 green (refusal + happy path)
- [x] `tests/positive/test_shelve_happy.py` — full adoption trail

---

## Notes for next builder

- **Inhale** = `fit_packet`; `init_db` on every wake (idempotent). Cites ids/paths only.
- **Compare** = `scan_ground_warnings` (drift + contradictions); `check_drawer` for one drawer
- **Shelving** = `inn/shelve.py` only — one crossing; `ground_path` in adoption meta.
- **Ground file** = `room.yaml` → `permissions.ground_file`; no hardcoded room paths in Python.
- **Contradiction scan** live in `compare.scan_ground_warnings` (within-room, cross-room, superseded-in-file).
- **Cold worker map** in HANDOFF.md — module → door → returns; `INHALE_PACKET` in `breath.py`.
- **Seams closed:** `session.yaml`, room↔bucket table, dual hash (`body_hash` + `content_hash`).
- **Schema authority:** `woods/schema.sql` here — FOREST.md is lineage only.
- Last real use: still none. Hostile tests 4 and 6 remain manual/eval work.

---

## Ancestry marker

Layer 0.5–2 notes preserved in git history and BUILD_SPEC/HANDOFF.

---

*Updated: 2026-07-05 — cold-worker pass before commit (layers 2–3).*
