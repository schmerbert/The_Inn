# logs/ — conversation lineage

Published session extracts. **Extraction-only:** tool calls, thinking blocks,
and harness plumbing are omitted; user and assistant words are kept.

Files are named `YYYY-MM-DD-slug.md` for GitHub legibility. Each file's
**Source** line keeps the original transcript id (matches `logs/.source/*.jsonl`).

| File | Builder | Pass | Notes |
|------|---------|------|-------|
| `2026-07-02-prebuild-mapping.md` | Claude | 1 | Main mapping — PREBUILD, inn cast, scribe/steward, forest |
| `2026-07-02-prebuild-mapping-compacted.md` | Claude | 1 | Continuation of mapping after context compaction (summary + tail) |
| `2026-07-02-marble-alignment.md` | Cursor | 1 | Familiarize repo; "same marble?" alignment; motion / exemplar compare |
| `2026-07-03-map-survey-first-push.md` | Fable 5 | 1 | MAP/PYRAMID cold read, burial (test 6), first-push inventory |
| `2026-07-03-repo-review-pass2-hardening.md` | Cursor | 2 | **Repo review** — GitHub fresh read, unveil/README; BUILD_SPEC, AGENTS |
| `2026-07-03-layer-1-bones.md` | Cursor | 2 | Immersion critique; rooms+breath; layer 1 build + doc cleanup |
| `2026-07-04-layers-2-3-gates-ground.md` | Cursor | 2 | Shelving, ground fitting, cold-worker pass, commit/push |

Raw `.jsonl` sources (unsanitized) live in `.source/` (gitignored, local only).
Run `python tools/sanitize_logs.py` after manual edits to published logs.

## Archive a new session

**Claude Code / Fable** (existing jsonl export):

```bash
python tools/archive_session.py path/to/session.jsonl
```

**Cursor** (agent transcript jsonl):

```bash
python tools/archive_session.py path/to/<uuid>.jsonl logs/YYYY-MM-DD-short-slug.md --note "Pass N — short label"
```

Pass an explicit output path for a readable filename; otherwise the tool uses
the jsonl stem (uuid). Copies source to `logs/.source/<uuid>.jsonl`, sanitizes
machine-local paths (`~`, `<user>`, `<claude-project>`).
