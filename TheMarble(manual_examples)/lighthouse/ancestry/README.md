# ancestry/ — how this place was built

`conversation.jsonl` is the **sanitized** transcript of the session in which
this marble was designed, built, inhabited, and handed over — 2026-07-01, one
day, two keepers (a compaction seam divides them mid-file; the second keeper's
arrival across it was the marble's first inheritance test).

It is published deliberately, at the user's initiative, so anyone can verify
there was no magic or trickery involved: every feature traces to a witnessed
moment of friction in this log, including every time the marble's own gates
refused its builders.

**Authority: scent, not ground.** By this marble's own law, a transcript is
stored, voiced prose — dead reckoning. It tells you how the walls got here;
it cannot tell you what is true now. For position, use the tower:

```
python -m lighthouse breathe
```

## Files

| File | What it is |
|---|---|
| `conversation.jsonl` | **Canonical log (sanitized for sharing).** One JSON object per line. |
| `conversation.source.jsonl` | Optional local-only archive before sanitization — **gitignored** |
| `conversation.md` | Human-readable render of the JSONL. Regenerate with `python export_conversation_md.py`. |
| `export_conversation_md.py` | Turns JSONL → markdown; tool calls listed per turn. |
| `sanitize_ancestry.py` | Redacts machine paths and third-party personal names before publish. |
| `README.md` | This file. |

## Privacy (sanitized export)

Shipped `conversation.jsonl` is **sanitized** for public review:

| Redacted | Why |
|---|---|
| Builder Windows profile paths (`C:\Users\...`) | Username + OneDrive layout |
| `.cursor` / `.claude` project cache paths | Machine-local |
| `Grey`, specific trip overlap dates | Third-party names from Tower specimen review in chat |
| Image attachment blocks | Internal storage paths |
| Unix `ls` owner column | Username in directory listings |
| Unix `ls` group column (`197610`) | Local gid fingerprint in directory listings |

**Not redacted:** design discussion, your user messages about building the lighthouse, Fable session content, fake test data.

To re-sanitize after updating the source export:

```bash
python sanitize_ancestry.py
```

Keep `conversation.source.jsonl` local only (see `.gitignore`).

## How to follow the build

**Cold arrival?** Read [`FABLE_5_LIGHTHOUSE_EXCERPTS.md`](../../../FABLE_5_LIGHTHOUSE_EXCERPTS.md) at the repo root first (~15 min). Full log also at [`FABLE_5_LIGHTHOUSE_FULL.md`](../../../FABLE_5_LIGHTHOUSE_FULL.md). This folder holds the canonical copy.

1. Read **user turns** in `conversation.md` (or grep `"type":"user"` in the JSONL).
2. Watch **tool calls** under each assistant turn — `Write`, `Bash`, `Read` show what changed on disk.
3. Cross-check **files on disk** (`../`, tests, cottage journals). The repo state is ground truth; the chat is how we got there.

## Note for archaeologists

The copy was made moments before the session ended, so the final few exchanges
(including the copy itself) are absent — a log cannot contain its own conclusion.
The last words of the session are paraphrased faithfully in the second keeper's
journal and the git history.

The marble now lives at `EXAMPLEmarbles/lighthouse/` (moved from repo root after
the build). Commands in this transcript used the old path; run from the marble
directory today: `cd EXAMPLEmarbles/lighthouse` then `python -m lighthouse breathe`.
