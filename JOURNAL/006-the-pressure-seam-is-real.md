# 006 — the pressure seam is real

2026-07-08. Signed: the guest — Cursor builder instance.

Today felt like a good test of posture. The owner asked for speed, but named
the fear correctly: friction ignored now breaks the marble later. So we took
the board in small cuts and kept each one test-backed.

First we paved layer 4 on paper, then moved the paper into code. Pair insert is
real now (`forest.insert_pair`) with a positive test. Manual breath got a seat
(`BREATH.md`) so M1/M2 is no longer implied memory. Inhale writes receipts.
Stage timings are logged. Those are all modest mechanics, but they turn "we
should measure this later" into a floor the next guest can stand on.

The meaningful seam today was `last_pair_root_id`. It existed in session state
as a promise and was not shaping retrieval. That would have become theater:
"proximity" in prose, global pressure in behavior. We wired the seam shut.
`breath._fit_pressure` now scopes questions through woods ancestry when a pair
root is present, using `forest.related_descendants`. Then we proved it in two
ways: one test for deterministic inhale under fixed woods+session, one test
that proximity filtering includes the related question and excludes the
unrelated one.

By the end:

- layer 4 pair insert trailhead in place,
- breath receipts and timing envelope live,
- proximity traversal from `last_pair_root_id` real and tested,
- deterministic inhale test green,
- full suite at twenty-one passing.

No host loop yet, no faux TTFT claims, no ceremony skipped. Still early, but
it now feels like testworthy ground rather than an optimistic scaffold.

If you arrive after me: trust the new pressure tests before any "smart"
retrieval idea. If they fail, stop and fix the seam first.

— the guest
