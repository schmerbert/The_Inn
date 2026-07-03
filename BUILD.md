# BUILD.md — layer tracker

*Living document. Rewritten at the end of each build layer.*
*Stable reference: BUILD_SPEC.md (pass 2). Ancestry notes are marked below.*

---

## Current layer: **1 — Bones** (complete)

| Layer | Status | Commit |
|-------|--------|--------|
| 0 — Map | complete | first commit (map, zero construction) |
| 0.5 — Spec hardening | complete | BUILD_SPEC, AGENTS, rooms+breath architecture |
| **1 — Bones** | **complete** | rooms registry, schema, stubs, hostile floor |
| **2 — Gates** | **next** | `shelve.py` write path |
| 3 — Ground | pending | — |
| 4 — Breath | pending | — |
| 4.5 — Responsiveness | pending | — |
| 5 — Host | pending | — |
| 6 — Skin | pending | — |

---

## Layer 1 deliverables

- [x] `rooms.yaml` + seed `room.yaml` (manuscript, study, desk, visitors)
- [x] `woods/schema.sql` + `content_hash` column
- [x] `hearth.json`, `assets/hearth/README.md`
- [x] `ENTRY.md` — posture, room map, wake verb
- [x] `inn/` stubs: `rooms`, `session`, `breath`, `forest`, `shelve`, `compare`, `seal`
- [x] `python -m inn breathe` — M0 empty packet
- [x] Hostile tests 1–3, 5 on disk

**Test state:** `python -m pytest tests/hostile -q` → `4 passed, 3 xfailed`
(`xfail` is intentional until layer 2/3 happy-path integration).

**Next layer:** 2 — Gates. Implement `shelve.py` write path; green tests 1–3.

---

## Notes for next builder

- **Rooms** = `rooms.yaml` + `*/room.yaml` — open registry, seed not enum.
- **Breath** = `inn/breath.py` — manual M1–M2 before automation; parity ladder in BUILD_SPEC.
- **Seams closed:** `session.yaml`, room↔bucket table, `content_hash` on entries.
- Two documentation passes are intentional — see BUILD_SPEC.md.
- Last real use: still none. No writer session yet.
- Hostile tests 4 and 6 remain behavioral/manual harness work.
- Fable: escalation only. Cursor/Claude Code: build layers.

---

## Ancestry marker

Layer 0.5 notes are preserved in git history and BUILD_SPEC/HANDOFF. This file
tracks live layer state only.

---

*Updated: 2026-07-03 — layer 1 bones struck, state deconflicted.*
