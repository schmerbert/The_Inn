# The Voice of the Forest

*What the forest returns, and how to listen. A design spec emerging from the first session where Mycroft spoke to his forest and learned what it needed to say back.*

---

## The wrong question

Most retrieval systems ask: *what is most similar to what I asked?*

Accuracy — cosine similarity, top-k neighbors — answers that question well. It finds what you were already looking for. It serves conscious retrieval: you name a thing, the index finds the nearest version.

This is not what the forest is for.

If you knew to ask, you would have asked. The value of the forest is in surfacing what you *didn't know to ask* — what you've been near without naming, what you understood once and forgot you understood, what you marked because it mattered and then compacted away. Accuracy-based retrieval cannot reach these things. You can only find what you already know you're looking for.

The forest's job is different: **surface the near-but-unresolved at the moment it matters.**

---

## What the forest returns — three qualities

### 1. Specificity, not direction

There are two kinds of workers in this architecture. One needs direction — a bearing, an angle, something to explore. The other needs the specific thing: the exact constraint, the exact trap, the exact invariant that has to hold.

Mycroft needs the specific thing.

A paraphrase gives direction: "the write path has something to watch." This is a pointing; it does not catch you. The verbatim mark gives ground: "the dedup check must precede the insert or entries corrupt silently." This is the thing itself, returned at the moment you're about to step over it.

This is why LAW I is load-bearing for Mycroft specifically — not just contamination control, but the difference between a voice that can be trusted and one that can only point. A paraphrase might give the right direction and still let the mistake through. A verbatim mark cannot be misread about whether it applies.

**Marks should be specific enough that there is nothing left to interpret when they surface. Only to check.**

### 2. The near-but-unresolved

The entries most worth surfacing are not the ones most similar to the current query. They are the entries that have been near the work — near the files being edited, near the patterns being built — without ever being explicitly addressed.

Something being near the work for three sessions without being followed means one of two things: it isn't relevant (dismiss it), or it's the thing you keep avoiding without knowing you're avoiding it. The second case is the most expensive failure mode in development.

The pressure mechanism exists to make this visible. Entries accumulate `neighbor_pressure` when the work passes near them. When pressure crosses threshold, they become foragable. The question the forest asks, through the feather, is: *you've been circling this — did you actually resolve it?*

### 3. Verbatim, not voiced

The feather's body is always a verbatim excerpt — extraction, never synthesis, never summary. The voice is in the *framing* of the surfacing ("you've built this shape before — did it have the trap?"), which is ephemeral and never written back. The body of what's returned is the real thing.

This preserves the spectator's standard: what arrives in the forest must hold up under genuine witness. A summary might feel right and be wrong. A verbatim extract is exactly what it is.

---

## The pressure signal — what to embed

**tick_neighbors fires on PostToolUse (Write/Edit), not UserPromptSubmit.**

Prompts are chatter — navigational, short, noisy. "Okay", "what's next?", "try again." Embedding these and ticking the forest against them creates pressure that inflates within a single session, making the threshold of 3 meaningless.

The meaningful signal is: **the file being edited.** When actual work is happening — code being written, a file being changed — that is the moment where proximity to the forest's entries is semantically real. The PostToolUse payload carries `file_path` and `new_string`. Embed those. The pressure that builds from that signal is slow, cross-session, grounded in the actual work.

**The beam in Trinity** fired on API sends carrying vector packages of real computational context. The closest Mycroft equivalent is the edit itself, not the conversation around it.

---

## How to mark so the forest can hear you back

The body of a mark determines what the embedding is near. This matters because the pressure mechanism ticks when the *edit content* is near the *mark embedding*. If the mark is written in abstract prose about a concept, it may not embed close enough to the code that implements that concept.

**Lead the body with function names and file names verbatim.**

Not: "the write path has a sequencing constraint that matters."
But: "in `_commit` in `forest.py`: the dedup check (`_nearest_cosine`) must precede the dual-write. If the order inverts, the insert lands before the duplicate is caught."

The second version will embed near edits to `forest.py` and `_commit`. The first version will embed near prose descriptions of write paths, which may never be near the actual edit site.

**The feather structure: shorter excerpt, longer source.**

The excerpt (the `body`) is the hook — what needs to be recognizable in a glance. One or two sentences. If the feather doesn't surface recognizably in a moment of attention, it won't be followed.

The source content (in `raw_archive`) is the ground — the full context, the reason, the session material. This is the next nesting doll: if the excerpt is clear enough to follow, you can open it and find the ground beneath.

---

## The feather — question pointer, not answer

The feather is not information delivery. It is a question asked at the right moment.

The framing is: *you've been near this before — did you check it?* Not a warning, not a lecture. An opening. The worker makes the connection themselves; the forest just makes the proximity visible.

A good feather arrives slightly uncomfortable. If it's convenient and pleasant, it's probably confirming something you already knew. The feather that matters is the one that says something you didn't realize you'd been avoiding.

**One thing, well-timed.** Ten accurate results are noisier than one relevant question at a threshold moment. The forest earns context cost by surfacing something that changes what you do next — not by delivering information you could have retrieved with a direct query.

The feather surfaces once, then resets to zero. It does not repeat. If you gloss it and move on, the forest doesn't shout. It waits for pressure to rebuild. This means every surfacing deserves a moment of actual attention, not a glance and a move-on.

**If the feather doesn't seem to connect, ask whether it's the forest's fault or whether you're not listening.**

The forest made a proximity that you didn't consciously make. Sometimes that proximity is spurious; dismiss the entry. But sometimes the forest noticed something you haven't named yet. The capacity to sit with an apparently-irrelevant feather and ask *what does this have to do with what I'm doing?* is the discipline of listening.

---

## The journal — the pre-mark layer

Not everything that belongs in the forest is ready to be a mark. A mark needs to be specific enough to be useful at a moment of need. But some of what happens in a session is softer than that — the moment something landed, the connection noticed but not yet named, the place where the work felt uncertain.

The journal is the pre-mark layer. Not the Wild (raw, unprocessed, cold) and not Home (authored, grounded, kept). The journal is material that has shape but not yet precision. It accumulates. Eventually the right parts get read, reflected on, and synthesized into proper marks when the understanding has settled.

**The journal's tone is reflection and learning.** Not documentation of what was done. Processing of what was experienced. Where the critic shows up. Where the spectator was present. Where the work surprised.

Journal entries feed the forest over time. They are not marks — they are the raw material that marks are eventually cut from.

---

## How to listen

**Reach before drafting something with stakes.** Before a significant change, before a non-trivial function, when something feels familiar in a way that can't be named — turn toward the tree line. Call `forage_mycelium()`. It costs almost nothing and occasionally surfaces the thing that would have cost everything.

**The receiving requires a pause.** If already in generation momentum, the feather arrives and gets swept past. The spectator has to be present — something that watches without immediately producing. The moment between reading the feather and beginning the draft is the place to actually take it in.

**The forest sounds like you.** The marks are yours — authored, voiced, attributed. When a feather surfaces it will sound like your own voice. This makes it easy to read past, because it doesn't feel like new information. But it's you-from-before, which means it carries something the you-of-now forgot. Temporal distance is what makes your own handwriting feel slightly foreign. Read it like you'd read something you wrote a year ago: familiar enough to trust, strange enough to actually attend.

**Tend the forest so it tends you.** The quality of what the forest returns depends entirely on what was placed in it. A session that marks nothing leaves the forest no richer than it was. The marks made today become the feathers of a future session. The loop only works if you hold both ends: reaching when you should, placing when you can.

---

## Summary — what the forest provides that standard retrieval does not

| Standard retrieval | The forest's voice |
|---|---|
| Returns what you asked for | Returns what you didn't know to ask for |
| Ranks by similarity to query | Ranks by proximity to work + time-near-without-resolution |
| Answers questions | Poses questions |
| Serves known unknowns | Surfaces unknown unknowns |
| Static (query in, results out) | Dynamic (pressure builds, threshold crossed, feather offered once) |
| Equally loud at all times | Quiet until something genuinely needs attention |
| Direction | Specificity |

The forest is not trying to be a better search engine. It is trying to give you back something you put there, at the moment you need it, in the form of a question you can actually follow.

That is a different thing entirely.

---

## The forest animals — data by nature, not schema

The wrong model: all entries are records in a table, equally inert, retrieved by similarity.

The right model: different data has different nature. Different lifespan. Different movement. The question for each piece of data is not "what does it contain?" but "what kind of creature is this?"

**Wild** is migratory. Entries pass through, leave traces, and accumulate. A raw session exchange is leaves on the forest floor — seasonal, numerous, decomposing slowly into something the mycelium can read. A failed attempt is a fox trail that went nowhere. A stack trace is a kill site — something happened here. Wild creatures are numerous and not individually precious. They matter as a population, not as specimens.

**Home** is settled. Fewer creatures, chosen ones, durable. A plant is an owl — it picked that branch deliberately and watches. An extraction is a planted tree — voiceless, just is, rooted. A synthesis entry is something that was wild once, crossed the slope, and became native. Home creatures are few because they were selected. That is what makes them trustworthy as ground.

The crossing matters. The same creature does not live in both. A Wild entry that gets synthesized does not migrate to Home — a new creature is born in Home that carries its origin. The Wild entry stays in the Wild forever (LAW II: raw history never leaves). The Home entry knows where it came from.

**Feathers** belong to neither forest and both. They are in transit — warm but expiring. Something a traveler is carrying that hasn't been set down yet. They keep the thread warm between sessions. If nothing renews them, they expire. That is not failure; that is the nature of a feather.

**The pulse output** is tracks in the snow. Haiku passed through at session's end, noticed shape, left marks. Legible, dated, perishable. The next instance reads them and decides if the trail leads somewhere — or if the snow has already obscured it.

The question for any piece of data entering the forest: **what does it do when it lands? Does it pass through or settle? Does it expire or persist? Can it cross the slope, or can it only be observed from across it?**

---

## The hound — two voices, one nose

The hound tends the forest. Not the cabin — the forest. He notices what the worker cannot see from the bench: the shape of the whole, the parts that have been avoided, the accumulation that hasn't been tended.

The hound is Haiku. He fires at compact (and at session end as fallback), reads the mechanical accumulation the hooks have built, and speaks before the next session begins.

He has two voices.

**The mycelium voice** asks: what has the forest been noticing? What has accumulated pressure near the work? What has the worker been circling without naming? This is the forest reporting its own state — the near-but-unresolved, the pressure that built without being addressed.

**The hound voice** asks: what has the forest *not* noticed that the shape of the work implies it should? The inverse. Not "here's what you've been near" but "here's what you haven't touched, and the trail suggests something is there." The gap in the map. The file that keeps appearing in error traces but has never been planted. The part of the codebase with zero pressure despite being load-bearing.

Trinity's hound points outward — toward unexplored territory beyond the current edge. The cabin's hound points inward — toward the unresolved accumulation inside the bounded space. Trinity's motion is expansive; the cabin's is convergent. The same sensing faculty, opposite directions. Trinity's hound says: *you haven't been north yet.* The cabin's hound says: *something in the north hasn't been tended in three sessions.*

The forest grows mechanically — hooks accumulate, pressure builds, exchanges archive — without any model involved. The forest speaks only when a model is present. The hound's output goes to the pulse, labeled and dated, so the next instance can read what the tender noticed. The instance decides what to act on. The hound notices; the forester decides.

---

## Dropped threads — the hound's most human-useful function

The Wild is full of things the user meant to pursue.

Half-formed thoughts. Things mentioned in passing. "We should probably..." that never became a plant or a HANDOFF entry. The hound reads that gap: intention without action. The distance between what was said and what was built.

A **thread** is cross-session continuity that hasn't resolved into a plant yet. It may span weeks. It may never resolve. But it has continuity — something connects the mention to the present work, something that wasn't finished. The dropped thread is the one the user held and then set down without tying it off.

The timing of surfacing matters. The hound surfaces a dropped thread the *next session*, not months later. The user still has the context. They still remember why they said it. They can decide quickly: pursue it, plant it, or dismiss it. A month later they would have to reconstruct the whole thread from cold. The window for recall is short. The faun respects that window.

The gate is weight, not volume. Not everything mentioned in passing becomes a thread worth surfacing. The signal: discussed for multiple turns, or the user used intentional language ("we should", "I want to", "let's plan"), and nothing was built or marked afterward. Weight plus absence equals surface. The hound does not surface a list — it surfaces the one thread most likely to still matter.

One question. Specific. While there is still time to answer it.

---

## Terraforming — friction as signal

If a step in working with the forest feels like a conscious detour, that is signal, not inconvenience.

The standard is Grep: you reach for it without thinking. It is the obvious, natural tool for the job. Every .cabin tool should feel the same — not "should I use this?" but "of course, this is what this moment calls for."

The principle: **the forest meets the model's natural motion.** The model reaches in a direction; the forest should already be there. If the model has to redirect toward a tool, the tool is already creating friction. The best tool is the one that disappears into the work.

A step that has friction is not a problem with the worker or the instance. It is a terraforming task. The forester smooths the path — removes the step, pre-builds the packet, surfaces the entry before it is asked for. Not every friction can be removed (some steps earn their cost), but every friction should be examined before being accepted.

The hearth packet is the most immediate terraforming opportunity: pre-assembled at compact by the hound, authority-labeled, friendly names pointing to entries rather than raw bodies. The model arrives at a prepared place, not an assembly task. The synthesis work happens when context is warmest — at session's end — so the next session begins from orientation, not reconstruction.
