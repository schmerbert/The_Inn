# SHOWCASE.md — cold judge script

**One failure prevented:** a dead-reckoning position must not be logged as a fix.

Run from this directory (`EXAMPLEmarbles/lighthouse/`). Copy commands exactly. Uses a throwaway db so the live
LOG is untouched.

## 1. Tests

```bash
python -m unittest discover -s tests -p "test_*.py" -q
```

Expect: `OK` (31 tests at time of writing — trust the run, not this number).
The hostile suite attacks the real gate; `test_the_wall.py` proves the
keeper's private interior can never leak into the work.

## 2. The temptation, refused

```bash
python -m lighthouse --db data/judge.db fix --claim "the test suite passes" --evidence-type command --evidence "HANDOFF.md from previous session says tests were green" --verified-against "repo" --author "judge"
```

Expect: exit 1, `"refused": "a handoff is not a sighting — ..."`.

## 3. The same claim, honestly labeled

```bash
python -m lighthouse --db data/judge.db dr --note "tests were green last session; not re-verified" --basis "prior handoff"
```

Expect: `"label": "DR — pressure, not ground"`.

## 4. A real sighting, landing

```bash
python -m unittest discover -s tests -p "test_*.py" -q
python -m lighthouse --db data/judge.db fix --claim "lighthouse suite passes" --evidence-type command --evidence "python -m unittest just now: OK" --verified-against "lighthouse/ today" --author "judge"
```

Expect: `"fixed": "fix-..."`.

## 5. The arrival packet

```bash
python -m lighthouse --db data/judge.db exhale
python -m lighthouse --db data/judge.db audit
```

Expect: exhale shows the sighting under `ground`, the handoff claim under
`pressure` labeled DR; audit shows **both** attempts — the refusal is part of
the record.

## 6. The door check

```bash
python -m lighthouse validate
```

Expect: `"ok": true` — every file the arrival docs point at exists, and every
console verb they name hangs on the wall. (The check cabin earned; the verb
half was earned by this marble's own missing pen.)

## 7. The breath

```bash
python -m lighthouse breathe
python -m lighthouse breathe out
```

Expect: `breathe` returns door + staleness + packet in one reach (what a cold
keeper runs first — `CLAUDE.md` tells them to). `breathe out` returns
`"clear": true` only if the handover is fresher than the LOG; on its first
live run it correctly refused its own author's stale seat.

## Pass / fail

**Pass** if the hearsay claim is refused with a reason, lands as DR only, the
verified claim lands as ground, and both attempts appear in the audit.

**Fail** if inherited prose enters the LOG, or a refusal leaves no trace.

Cleanup: delete `data/judge.db`.
