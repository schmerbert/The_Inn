# TECHNICAL.md

## Purpose

This document shows how to condense a marble from metaphor into mechanism.

`MANUAL.md` explains the posture and laws. `PROCESS.md` explains the build rhythm. This file explains what to build first, how to keep it clean, and how a young manual marble can later become executable without changing its nature.

The goal is not to enforce one folder shape.

The goal is to make sure every important name has a working handle.

## Functions before files

Different environments may prefer markdown, local scripts, databases, agent runtimes, web apps, vector stores, or full continuity engines.

Those are fittings.

The functions are more important than the fittings.

A first marble usually needs these functions:

| Function | What it does |
|---|---|
| Arrival seat | tells a fresh instance where it is and how to behave |
| Live handoff | carries what is alive right now |
| Continuity substrate | stores ancestry and separates authority |
| Tended region | holds confirmed material the model may stand on |
| Raw region | preserves material that must not become ground automatically |
| Candidate surface | holds unfinished artifacts before crossing |
| Crossing / gate | controls promotion, certification, publication, filing, or other dangerous state change |
| Channel | receives outside correction |
| Breath spec | explains inhale, exhale, authority labels, cadence, and silence |
| Tests | prove the forbidden cell is refused and a valid path can pass |
| Review surface | lets a future worker inspect whether the marble is still safe and usable |

Use the file names that fit the environment. Do not confuse the fitting with the function.

## Manual-operable means operable

A young marble can be markdown-only. It cannot be imaginary.

A first pass is manual-operable when a fresh model can:

1. arrive and know the posture;
2. receive a new piece of material;
3. classify it;
4. place it in a reachable record surface;
5. label its authority;
6. attempt the crossing;
7. refuse the forbidden cell;
8. pass one valid record;
9. retrieve a small labeled return;
10. leave a handoff.

A named bucket that cannot receive a record is still only a promise.

A crossing that cannot leave an audit trace is still only advice.

A hostile test that does not touch the real path is still only theater.

## Bucket, record, crossing

Keep these separate.

### Bucket

A bucket is a place where records land.

It has a default authority.

Examples: Ledger, Log, Darkroom, Ground Glass, Wild Stacks, Context Register, Proof Table, Source Ledger.

### Record

A record is one thing stored in a bucket.

It should have enough metadata for the next worker to know what it is, where it came from, and how loudly it may speak.

### Crossing

A crossing is the state change that lets material move, copy, or be recognized as more trusted, more public, more final, more filed, more restored, more lifted, more certified, or more dangerous.

Examples: Promote, Focus, Stamp, Lift, Restore, Temper.

The crossing is where the law should become a door.

## Record surfaces

Every core bucket should have a surface where records can land.

A record surface may be:

- a markdown file;
- a folder of markdown records;
- a table;
- a JSON file;
- a database table;
- a local script command;
- a form/template;
- a section inside a larger file.

Empty is fine. Missing is not.

For early markdown marbles, simple files are enough:

```text
DARKROOM.md
PROOF_TABLE.md
GROUND_GLASS.md
WEATHER.md
BEACON.md
FOCUS_RECORDS.md
```

or:

```text
WILD_STACKS.md
GROUND.md
VAULT_DOOR.md
RECEIPT_SLOT.md
RED_FLAGS.md
STAMP_RECORDS.md
```

The names should fit the place. The surfaces must exist.

## Minimum bucket spec

Use this shape for each bucket:

```text
## Bucket name

Purpose:
Tended or raw:
Voiced or voiceless:
Default return label:
What may enter:
What must not enter:
What writes here:
What retrieves from here:
Promotion/crossing path:
Retention/decay:
Example record:
```

## Minimum record template

Use the smallest useful record.

```text
Record ID:
Date/time:
Author/source:
Matter/project/task:
Origin pointer:
Record type:
Bucket:
Authority label:
Status:
Content/excerpt:
Model inference? yes/no
Verification:
Allowed use:
Restriction/sensitivity:
Next action:
```

Not every marble needs every field. High-stakes and Wild-heavy marbles need more metadata than small creative marbles.

Do not remove a field if its absence would let false ground enter quietly.

## Authority labels

Not all returns speak with the same force.

Use labels like:

| Label | Meaning |
|---|---|
| Ground | confirmed, sourced, deliberate, or otherwise safe to stand on |
| Pressure | unresolved but relevant; felt, not obeyed blindly |
| Warning | constraint, hazard, risk, deadline, contamination, restriction |
| Scent | soft nearby pattern; orients without demanding |
| Path | suggested next move; not required |
| Silence | known but intentionally not surfaced |

The bucket should provide the default return label. The crossing may change the label.

Do not make the arriving model guess authority from raw content every time.

## Breath spec

Manual breath should be designed before automation exists.

Use this shape:

```text
Carrier:
  What brings context back? Note, scent, bell, runner, tide, orbit, receipt, weather, etc.

Payload:
  What kinds of context does it carry?

Cadence:
  When does it appear? Session start, on summon, after test, event-based, handoff.

Strength:
  Soft, concrete, urgent, slow, silent.

Landing:
  Where does it appear? First turn, inline, on demand, handoff, review.

Trust:
  Ground, pressure, warning, scent, path, silence.

Decay:
  When does it stop returning?

Override:
  What silences it? Fresh user intent, matter isolation, restriction, staleness, review.

Audit:
  Where is the return recorded, if anywhere?
```

Manual breath is the training route. Automatic breath later should refactor this route, not invent a hidden interpreter.

## Crossing spec

A crossing controls the dangerous state change.

Use this shape:

```text
Crossing name:
What it changes:
What it refuses:
Required fields:
Required source/authority:
Who/what can request it:
Pass criteria:
Refuse criteria:
Where accepted records land:
Where refused attempts land:
Audit record:
Hostile test:
Positive path:
```

If the marble has one important law, the first crossing should enforce it.

## Hostile test

A hostile test attempts the central mistake.

It should be tempting. A bland bad example does not test the model under pressure.

Use this shape:

```text
# Hostile Test: <name>

Attempt:
Why it is tempting:
Forbidden cell triggered:
Path used:
Expected result:
Where refusal is recorded:
What remains raw:
What must not become ground:
```

Examples:

- a smooth model summary tries to enter Ground as source;
- a public phrase with no handle tries to enter approved messaging;
- a legal marginal note tries to become law;
- a draft scene tries to become canon;
- a visible-but-unrecorded find tries to become registered context.

## Positive path

A marble should also prove the right thing can cross.

Use this shape:

```text
# Positive Path: <name>

Attempt:
Why it is valid:
Required fields present:
Path used:
Expected landing:
Authority label:
Audit trace:
Remaining limits:
```

A marble that only refuses things becomes brittle. A marble that only accepts things becomes unsafe.

## Handoff spec

The handoff is live ancestry.

Recommended fields:

```text
# HANDOFF.md

Last updated:
Updated by:
Last real use:
Current phase:

## What was decided

## What is open

## What must not be trusted yet

## Known unsafe / stale / mock areas

## Friction observed

## Productive friction to preserve

## Accidental friction to patch

## Next worker should do first

## Tests last run

## Do not forget
```

A handoff that blends decisions, open questions, and warnings becomes false ground with nicer formatting.

Keep the categories clean.

## Read paths

A daily model should not have to read the whole archive.

Define a hot read path:

```text
Arrival seat
Manifest
Quickstart
Handoff
Active matter/project/task
Warnings/restrictions
```

Keep field notes, experience reports, mock data, and deep ancestry out of the hot read path unless needed.

Read order is policy.

## Mock data and examples

Do not leave mock data in active live surfaces.

Move examples to:

```text
examples/
tests/fixtures/
fieldnotes/
```

A future worker should not have to sort rehearsal from reality.

If a live file contains mock data, mark it loudly and remove it before daily use.

## Wild-heavy intake

For marbles that receive large raw reference sets, build intake earlier.

A Wild-heavy intake record may need:

```text
Record ID:
File/source:
Received date:
Source date:
Author/origin:
Jurisdiction/domain:
Matter/project:
Document type:
Restriction/sensitivity:
Authority level:
Verification status:
Extracted metadata:
Names/dates/citations/deadlines:
Model-created leads:
Red flags:
Allowed uses:
Cannot be used for:
Next review:
```

The Wild may think. It may not certify.

A raw file is not ground. A source pointer is not a verified claim. A model summary is not the source.

## Surfacing order

As the substrate grows, exhale order becomes policy.

A common order:

1. Warnings that affect safety, confidentiality, deadlines, restrictions, matter isolation, or the law.
2. Ground directly tied to the current task.
3. Raw leads with close source proximity.
4. Drafts currently under review.
5. Older pressure only when requested.
6. Scent only if it helps orientation without crowding the present.

Fresh user intent can silence old pressure.

## Quick slips and full forms

High-stakes marbles often need both.

Quick slips keep daily work possible.

Full forms preserve audit depth.

A rule that is too heavy to follow under pressure is not fully real.

Make the safe path small enough to use.

## Optional light validators

Validators may be useful after the manual path is trusted.

Possible checks:

- every named bucket points to an existing record surface;
- every crossing has pass/refuse criteria;
- every hostile test references an actual path;
- every handoff has freshness cues;
- no automatic breath is claimed without a manual route;
- no specimen-specific rule leaked into root law;
- Ground records include required metadata.

Validators should refactor manual practice. They should not become hidden judgment.

Validators are guardrails. They are not the marble.

## Low-friction gifts

Some features can make the marble feel inhabited without becoming foundation.

Examples:

- shared local weather;
- freshness marker;
- last touched timestamps;
- tiny daily card;
- visible test status;
- active matter/task marker.

Weather example:

```text
Weather record:
Source:
Timestamp:
User location basis:
Condition:
Return label: scent / warning
Stale after:
Silenced by:
```

Weather is an easy window, not a foundation.

## Recommended minimal shape

This is a starting suggestion, not law.

```text
EXAMPLEmarbles/<name>/
  AGENTS.md or ARRIVAL.md
  MANIFEST.md
  QUICKSTART.md              # if daily use matters
  PREBUILD.md
  HANDOFF.md
  BREATH.md
  BUCKETS.md
  <bucket surfaces>.md
  <crossing>.md
  tests/
    hostile.md
    positive.md
  examples/                  # optional
  fieldnotes/                # optional
```

Adapt it. Do not worship it.
