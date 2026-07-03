# logs/ — conversation lineage

Published session extracts. **Extraction-only:** tool calls, thinking blocks,
and harness plumbing are omitted; user and assistant words are kept.

| File | Builder | Pass | Notes |
|------|---------|------|-------|
| `6cfa6540-…` | Cursor | 1 | Early repo familiarize + marble compare |
| `9c9e7a5c-…` | Claude | 1 | Mapping session (compaction summary) |
| `cf5505ab-…` | Claude | 1 | Main mapping — inn cast, PREBUILD |
| `b73c4c93-…` | Claude | 1 | Second stay / FOREST |
| `e50495bc-…` | Fable 5 | 1 | Third stay — MAP survey, PYRAMID, tests 5–6 |
| `d0aae6a7-…` | Cursor | 2 | Builder hardening — BUILD_SPEC, AGENTS, unveil |
| `f35f9d8e-…` | Cursor | 2 | Layer 1 bones — rooms, breath, hostile floor, doc cleanup |

Raw `.jsonl` sources (unsanitized) live in `.source/` (gitignored, local only).
Run `python tools/sanitize_logs.py` after manual edits to published logs.

## Archive a new session

**Claude Code / Fable** (existing jsonl export):

```bash
python tools/archive_session.py path/to/session.jsonl
```

**Cursor** (agent transcript jsonl):

```bash
python tools/archive_session.py path/to/<uuid>.jsonl --note "Pass N — short label"
```

Writes `logs/<stem>.md`, copies source to `logs/.source/<stem>.jsonl`, sanitizes
machine-local paths (`~`, `<user>`, `<claude-project>`).
