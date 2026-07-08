# BREATH.md — manual breath ladder (layer 4 reference)

This file is the manual parity spec for breath growth.
Automation in layer 5+ must match this procedure, not replace it semantically.

## M1 — manual inhale

1. Read `.inn/session.yaml` (`current_room`, `proximity`, `files_in_flight`).
2. Read `rooms.yaml` + current `<room>/room.yaml` posture/permissions.
3. Read `hearth.json` (`standing_context`).
4. Run compare warnings on ground rooms (drift + contradiction warnings).
5. List relevant ground adoption ids/paths from proximity.
6. List open questions (`question` bucket) near proximity.
7. Copy seam fields (`files_in_flight`, `last_pair_root_id`).
8. Write a receipt in `logs/breath/` (slot ids/counts only; no prose).

## M2 — manual exhale

1. Ensure new session messages are inserted in woods custody.
2. Run seat freshness check before rewriting `HANDOFF.md`.
3. Rewrite HANDOFF texture citing ids/paths (no body copy).
4. Update seam in `.inn/session.yaml`.
5. Write exhale receipt in `logs/breath/` (trailhead; layer 5 implementation).

## Diegetic latency classes (4.5 target)

- `<300ms`: silent nod (no announcement)
- `300ms–2s`: one-drawer check
- `2s+`: staged "let me check…"
- crossings: deliberate pace (Shelving never rushed)

## Notes

- `inn.breath.inhale()` is currently deterministic M0.5 fitting.
- `inn.breath_ledger` is the layer 4 receipt trailhead.
- Host TTFT and streaming gates start in layer 5.
