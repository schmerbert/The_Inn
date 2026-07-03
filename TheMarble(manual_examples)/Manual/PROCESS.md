# PROCESS.md

## Purpose

This file gives the build rhythm for making a marble.

It exists because many agents jump straight from request to files. That instinct is useful once the target is already known — but marble-making needs a wider first movement.

The first act is not the folder tree.

The first act is finding the place.

Beauty is allowed early. Authority must be earned. Keep that in your pocket as you read the rest of this file — it's the tension the whole rhythm is built to hold.

## The rhythm

```text
Widen
  ↓
Pre-Build Note
  ↓
Condense names
  ↓
Build manual surfaces
  ↓
Add hostile and positive tests
  ↓
Use once
  ↓
Classify friction
  ↓
Patch smallest surface
  ↓
Rewrite handoff
```

This is not gospel. It is the common path.

## 1. Widen

Tell the user, plainly:

```text
Before I build, let's find the place.
We need to know what repeated work this marble holds,
what goes wrong when it is careless,
and what kind of world would help a future model behave under pressure.
It can be playful. The play is not decoration; it is how we find the mechanism.
If a metaphor doesn't change behavior, we'll drop it — no hard feelings.
```

Widening is work, but it can also be the fun part. This is where you get to try a place on and see if it fits.

During widening, try several almost-right places. Rejecting a metaphor isn't a failure — it's useful, because it clarifies posture. Every place you set down teaches you something about the one you'll keep.

Ask:

- What repeated work will happen here?
- What will the future model need to inherit?
- What actually breaks if this goes wrong?
- What status should the model have?
- Where is the model allowed to stand?
- What should the model never claim to possess or know?
- What is raw material here?
- What is trusted ground here?
- What outside world corrects this place?
- Which names change behavior?

Don't rush past the cost. The cost is where the forbidden cell gets its face — and honestly, it's often where the marble starts to feel real.

## 2. Pre-Build Note

Before creating the marble's main files, write a visible Pre-Build Note in chat or in `PREBUILD.md`.

A Pre-Build Note is not final design. It's the bridge from exploration to building — a sketch, not a blueprint.

Use this shape:

```text
# PREBUILD.md

## Work
What recurring work will this marble hold?

## Cost
What actual damage happens when the marble is careless?

## Forbidden cell
What is the named version of false ground in this marble's language?

## Place
What place-shape fits the work? What almost-fit shapes were rejected, and why?

## Model posture
Where is the model allowed to stand? What role must it not inflate into?

## Tended / raw split
What can be stood on? What must be preserved but not trusted?

## Channel
How does outside correction enter?

## Manual breath
How does the young marble inhale, classify, store, retrieve, and label returns by hand?

## Core buckets and write surfaces
What named buckets exist, and where can each receive records?

## Crossing
What dangerous state change does the crossing control? What passes? What refuses?

## Hostile test
What tries to force the forbidden cell into trusted ground?

## Positive path
What valid record should be allowed to land?

## First use
What small real task will test the marble after the first pass?
```

A pre-build note can be short. It just needs to be specific enough to keep you from drifting into folder-shaped busywork.

## 3. Condense names

For every name, ask for its policy shadow.

```text
Name:
What does it store?
What does it refuse?
What does it return?
What does it warn about?
What behavior changes when it appears?
What writes to it?
What authority does it carry?
What test proves it matters?
```

The name doesn't have to be poetic. It has to be usable — though there's nothing wrong with it being both.

A name the model admires but can't act from is decoration. That's fine as an idea, but it isn't infrastructure yet.

A name that changes what the model stores, refuses, returns, or warns about — that's infrastructure. That's the name that earned its authority.

## 4. Build manual surfaces

Manual-first doesn't mean descriptive-only.

Build the smallest set of surfaces that lets a fresh model perform the marble today.

At minimum, the first pass should usually include:

```text
AGENTS.md or local arrival seat
MANIFEST.md
HANDOFF.md
BREATH.md
BUCKETS.md or bucket files
CROSSING.md or crossing file
tests/hostile.md
tests/positive.md
```

Use the file names that fit the environment. The function matters more than the fitting.

Each core bucket needs a write surface. This may be a markdown file, folder, table, JSON record, template, or script.

Empty is fine. Missing is not.

## 5. Add hostile and positive tests

A hostile test tries to force the central mistake into trusted ground.

A positive path proves the right thing can cross and land.

The hostile test should touch the same path real work will use — a conceptual warning alone won't tell you much.

Example hostile shape:

```text
Attempt:
Why it is tempting:
Expected refusal:
Where refusal is recorded:
What remains raw:
```

Example positive shape:

```text
Attempt:
Why it is valid:
Required fields present:
Expected landing:
Authority label:
Audit trace:
```

A marble should prove both that the wrong thing is refused and that the right thing has somewhere good to go.

## 6. Use once

After the first pass, use the marble on a real small task.

Not a complete production task. Something small, but with real pressure behind it.

Examples:

- turn messy internal material into a Reddit post;
- triage one uploaded reference document;
- inspect one household symptom;
- classify one research note;
- promote one confirmed writing fact into canon;
- attempt one codebase handoff.

Don't skip this step. The first use is where ancestry stops being an idea and becomes literal.

## 7. Classify friction

After first use, write down what happened.

Separate productive friction from accidental friction.

Productive friction:

- slows a dangerous crossing;
- forces source, audience, context, jurisdiction, matter, attribution, or uncertainty;
- protects the law;
- should usually remain.

Accidental friction:

- missing storage surface;
- unclear read path;
- too-heavy form for daily use;
- bucket too broad to act from;
- mock data mixed with live state;
- model must improvise where something goes.

Patch accidental friction with the smallest honest surface.

Don't remove productive friction just because it feels heavy. A gate is supposed to feel like a gate.

If the **same productive friction keeps returning** after honest patches — the simple form is working, but strain is showing in a specific place — check whether the pressure already has a name on the shelf: [`Reference/ADVANCED_MARBLES.md`](../Reference/ADVANCED_MARBLES.md) **§1** (symptom table). Open selectively; read one section; answer the Gate questions there. Not cover to cover. Not before the first pass works.

Fall and Lighthouse both opened the shelf mid-build, borrowed selectively, and *declined* most patterns. That's correct use.

## 8. Patch smallest surface

When friction appears, resist the urge to redesign the whole marble.

Build the smallest surface that makes the safe path usable without weakening the law.

A draft table may be enough. A quick slip may be enough. A source field may be enough. A triage card may be enough. A status label may be enough.

Use the smallest honest surface that preserves the law — small patches keep the marble easy to trust.

If smallest patches aren't enough and the strain is **recurring**, don't add rooms or automation yet. Classify the friction (step 7), then consult the friction shelf (§1 table in `Reference/ADVANCED_MARBLES.md`) before building a bigger surface. Record considered patterns — adopted or declined — in handoff or an `IDEAS.md` (see Lighthouse specimen).

## 9. Rewrite handoff

End by rewriting `HANDOFF.md`.

A good handoff separates:

```text
What was decided
What is open
What must not be trusted yet
What friction appeared
What changed because of friction
What the next worker should do first
Known stale or mock areas
Last real use
```

The handoff isn't a story about how the work went. It's the live state the next worker inherits — the thing that lets them arrive better off than you did.

## Optional: field note

If the marble taught the starter something, write an experience or field note.

Don't put every field note into root law right away. Field notes are ancestry and pressure — they're allowed to just sit and mean something for a while.

They let one marble teach the flock without becoming a cage.

## Common failure patterns

None of these mean the marble is broken. They're just the familiar shapes friction tends to take — worth knowing so you recognize them quickly.

### Folder-first drift

The model builds a neat folder tree before finding the cost.

Correction: write `PREBUILD.md` first.

### Beautiful but inoperable

The marble has lovely names and clear laws, but no record surfaces to actually receive anything.

Correction: every bucket needs a place to receive records.

### Hostile test theater

The hostile test proves the idea, but doesn't touch the actual path.

Correction: run the hostile test through the same crossing/storage route real work will use.

### Heavy safety

The marble has full forms so heavy that a future worker will just skip them.

Correction: add quick slips/cards while preserving full templates for audit depth.

### Specimen leakage

A lesson from one marble becomes root law too early, before it's proven it belongs everywhere.

Correction: keep field notes as pressure until repeated use proves portability.

### Horizon building

The model adds rooms, automation, validators, APIs, or advanced movement before manual use has earned them.

Correction: show the horizon, but build the floor first. There's no rush — the horizon will still be there.
