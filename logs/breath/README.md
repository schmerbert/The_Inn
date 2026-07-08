# logs/breath — inhale receipt trailhead (layer 4)

Append-only receipts for wake fitting. One JSON file per wake.

Receipt scope:
- slot ids / adoption ids only (no prose bodies)
- slot counts (`warnings`, `ground`, `pressure`)
- optional `timings_ms` envelope (layer 4.5+)

Writer-facing narrative stays in `HANDOFF.md`; this folder is clinical trace.
