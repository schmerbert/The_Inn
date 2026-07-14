# logs/breath — inhale receipt trailhead (layer 4)

Append-only receipts for wake fitting. One JSON file per wake.
`*.json` are gitignored (local traces); this README is committed.

Receipt scope:
- slot ids / adoption ids only (no prose bodies)
- slot counts (`warnings`, `ground`, `pressure`)
- optional `timings_ms` envelope

Writer-facing narrative stays in `HANDOFF.md`; this folder is clinical trace.
