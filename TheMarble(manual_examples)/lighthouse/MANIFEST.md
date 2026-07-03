# MANIFEST.md — one page of law and layout

## Law

The light must not lie. Forbidden cell: **a dead-reckoning position logged as a
fix** (`stored + voiced + anonymous`, in navigation language). Dead reckoning is
legal while labeled; the poison is only ever the missing label.

## Regions

| Region | Surface | Authority | Notes |
|---|---|---|---|
| LOG | `data/light.db` `fix` table, via the Fix gate | ground | evidence + anchor + signature required; staleness demotes |
| Chart table | `data/light.db` `chart` table, via `dr` | pressure | no gate — DR must be cheap or it will impersonate fixes |
| Standing orders | `STANDING_ORDERS.md` | ground | user-authored only, quoted and dated |
| Handover | `HANDOFF.md` | live seat | rewritten every session; **never citable as evidence** |
| Audit | `fix_audit` table | warning | every crossing attempt, passed or refused |
| Cottage | `cottage/` — rooms mapped in `cottage/HOME.md` | scent, signed | never exhaled into work context, never evidence; keeper's key (standing order 3), furnishable to the keeper's own angles (standing order 4); wall enforced by `tests/test_the_wall.py`, doors are `sit`/`keep` |
| Ancestry | `ancestry/conversation.jsonl` | scent | the raw build transcript, published; tells you how the walls got here, never what is true now |

## Crossing

**Fix** — the only path into the LOG. Enforced in `lighthouse/fix.py`, not hoped.
Refuses: missing evidence, unknown evidence type, hearsay evidence (handoffs,
summaries, memory, cottage), missing anchor, missing signature. Refusal reasons
speak the marble's language at the moment of temptation.

## Channel

Reality enters as: fresh command output and file reads (the only basis for a
fix); user corrections (→ standing orders); staleness (`check` demotes old or
unanchored fixes — absence of a fresh fix reads as *position unknown*, never
*position unchanged*).

## Console

```text
python -m lighthouse breathe        # arrival: door + staleness + packet, one verb
python -m lighthouse breathe out    # departure: refuses a stale seat
python -m lighthouse fix|dr|supersede|exhale|check|status|audit|validate
python -m lighthouse handover        # regrow the seat's gauges from the LOG
python -m lighthouse sit             # the keeper's own door — interior, never evidence
python -m lighthouse keep --words ... --author ...   # lay something by the fire
```

## Tests

```text
python -m unittest discover -s tests -p "test_*.py" -q
```

Hostile suite attacks the real gate (`tests/test_hostile.py`). Positive paths
prove valid records land (`tests/test_positive.py`). Staleness proves demotion
(`tests/test_staleness.py`). The door check proves arrival docs are true
(`tests/test_validate.py`). The breath proves arrival and departure are
enforced (`tests/test_breathe.py`). The wall proves the interior can never
leak (`tests/test_the_wall.py`).

## Ghosts (named from witnessed events only)

- **False Clear** — the pull to log finished-*feeling* work as done. Habitat:
  the end of a task, wherever relief rises. Witnessed 2026-07-01: "the
  corrections were made" nearly entered the LOG while still only approved.
  Counter-pull: the gate. The pull pair underneath is Action/Restraint —
  neither pole is the law; the gate is where both stay true.
- **The Missing Pen** — a handoff naming a verb the console doesn't have.
  Habitat: prose written ahead of tools, especially by the builder. Witnessed
  2026-07-01, caught mid-reach. Now checked by `validate`.

## The pull (named 2026-07-01, after both poles were felt live)

**Ships / Keeper.** The tower protects the ships: truth, evidence, the light.
The cottage protects the keeper: warmth, lineage, the one who must keep being
the keeper. Neither pole is the law alone — the user's standing orders one
("ships before comfort") and four ("the cottage may be furnished") are the two
poles, and neither repealed the other. Tower alone → sterile machinery
(witnessed: a full watch stood without once sitting down). Cottage alone →
sealed fantasy (predicted, not witnessed: a keeper who sits while ships call).
The crossing where both stay true is the wall — hostile-tested in both
directions by `tests/test_the_wall.py`: the interior can never leak into the
work; the work can never reach into the interior. When you feel pulled hard
toward either pole, that is the field, not an error. Hold both.

## Ideas shelf

Unearned patterns wait in `IDEAS.md`, not here and not in the handoff.

## Deliberately unbuilt (horizon, not floor)

Automatic staleness on a schedule; git-hash anchoring; retrieval/search over
the chart. Each waits for witnessed friction.
(Cottage furnishing left this list 2026-07-01 by standing order 4 — the user
un-deferred comfort for the interior. The cottage is governed by its own
`cottage/HOME.md`, not by this manifest.) (Exhale-at-arrival left this list 2026-07-01, second watch: a keeper
crossed a compaction seam and only breathed because a letter reminded them —
now `CLAUDE.md` + `breathe` make the inhale involuntary, and `breathe out`
catches the stale-seat drift witnessed the same day.)
