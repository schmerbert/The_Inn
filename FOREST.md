# THE FOREST — a retrieval base anyone can use

*A generic, reusable memory store for AI continuity environments ("marbles").
Think of it as the power supply in a computer: one sealed unit, connections
everywhere, you use the ones you need. This document is the template. The
woods behind The Dog-Ear (this repo's marble) are its first instance.*

*Written 2026-07-03, from the mapping sessions. Ancestry: Trinity/HomeGlobe
Spec 10 (Three Forests), the Marble Manual trilogy, and the conversation
preserved in this repo's logs — the full discussion that produced it.*

---

## Why current RAG disappoints

The standard configuration — chunk → embed → cosine → stuff context — throws
away structure at every step:

1. **Chunking severs ancestry.** A chunk doesn't know what it came from, what
   preceded it, or what it was said in response to. It is an amnesiac quotation.
2. **Similarity is the only law.** No concept of *who* said a thing, *when*,
   whether it was retracted, whether it was ground truth or a stranger's
   opinion. A superseded fact and its replacement retrieve side by side with
   equal confidence.
3. **Relevance is assumed to be semantic.** The most valuable retrievals in
   long work are often causally related and semantically distant. Cosine never
   finds them.
4. **Retrieval is stateless.** Nothing learns from being retrieved. No worn
   paths, no history of what mattered.

The diagnosis in one line: **RAG systems fail because they store text and
discard custody. Store custody and the text takes care of itself.**

The forest's answer is four small mechanisms with one job each, instead of one
embedding index doing all four badly:

| Mechanism | Job | One line |
|---|---|---|
| Buckets | scope | what is in play right now |
| Search (FTS5) | find | entry points into the store |
| Ancestry | certify | where did this come from |
| Wander | surprise | connections you didn't ask for (a cable, later) |

## The constitution

The forest is not a database schema with rules attached. The rules ARE the
product; the storage is commodity. Four laws:

1. **Append-only.** Nothing is deleted, nothing is rewritten. Revision is
   supersession: the old entry remains, pointing at what replaced it. It stays
   true without staying ground.
2. **Everything is signed.** Every entry carries who produced it. Retrieval
   always returns entries *wearing* their signatures. An unsigned entry is
   refused at the door.
3. **Everything has ancestry.** Every entry carries an origin edge — the
   conversation it fell out of, the source it was imported from, the entries
   it was derived from. An orphan entry is refused at the door. This makes the
   worst failure — invented content wearing borrowed authority — *mechanically
   detectable*: a fact that cannot walk back to its origin was never a fact.
4. **Nothing is promoted by similarity.** Authority changes only through an
   explicit, recorded act by whoever holds authority (in a writer's marble:
   the author's quoted adopting words). The store may *think*; it may not
   *certify*.

## Core schema

One local sqlite file. Two tables plus FTS5. That is the whole core.

```sql
CREATE TABLE entries (
  id            INTEGER PRIMARY KEY,
  created_at    TEXT NOT NULL,          -- ISO 8601
  forest        TEXT NOT NULL,          -- 'home' | 'wild' | (mycelium is not writable)
  bucket        TEXT NOT NULL,          -- source_type, see below
  signature     TEXT NOT NULL,          -- who: 'author' | 'model' | 'visitor:George' | 'faun' | 'source:<url>'
  authority     TEXT NOT NULL,          -- 'ground' | 'model' | 'stranger' | 'hearsay'
  visibility    TEXT NOT NULL DEFAULT 'open',   -- 'open' | 'hidden' | 'deep' | 'sealed'
  superseded_by INTEGER REFERENCES entries(id), -- NULL = current
  body          TEXT NOT NULL           -- verbatim. never a summary of something else.
);

CREATE TABLE edges (
  from_id INTEGER NOT NULL REFERENCES entries(id),
  to_id   INTEGER NOT NULL REFERENCES entries(id),
  kind    TEXT NOT NULL   -- small closed vocabulary, see below
);

CREATE VIRTUAL TABLE entries_fts USING fts5(body, content=entries);
```

**Edge kinds — keep the vocabulary closed and small.** A rich edge taxonomy is
similarity wearing a graph costume. Six kinds, add a seventh only under
protest:

- `spoken_in` — entry precipitated out of this conversation pair
- `responds_to` — pair-to-pair conversational linking
- `derived_from` — synthesis pointing at its sources
- `adopts` — an adoption record pointing at what was adopted
- `supersedes` — new ground pointing at old (mirror of `superseded_by`)
- `cites` — a claim pointing at hearsay it leans on

**Insert discipline (the whole API, day one):** an insert without a signature
fails; an insert without at least one origin edge fails (the only exception:
conversation pairs themselves, which are roots); supersession is atomic — the
write that lands new ground writes `superseded_by` on the old in the same
transaction. Old canon isn't "carried out" by anyone; it *falls*, like a leaf
when the season turns, and lands where everything else already lies.

## Conversation pairs are the trunk

Almost nothing is *born* anywhere else. Facts are extracted from moments in
conversation; drafts are written in response to requests; adoptions ARE
exchanges. So pairs must be first-class rows **inserted as the session
happens** — their IDs must exist in real time, because every other write
during the session wants a parent. Log the conversation eventually and you
have a diary; grow it as a trunk and everything else grafts on.

This is the property that cannot be retrofitted. Edge discipline at write
time is nearly free; reconstructing ancestry later is impossible.

## Buckets — pollution control by exclusion

Buckets are the entry's *kind* (`source_type`). Reference set — rename freely,
the mechanism is what matters:

`session_pair, draft, superseded_canon, visitor_words, note, hearsay,
synthesis, question, adoption_record, import`

A retrieval scope is a set of open buckets — a `WHERE` clause, nothing more.
A closed valve cannot leak, whereas a downweighted result still sneaks into
context on a good cosine day. When a whole *category* pollutes, close its
bucket; when one *entry* smells wrong, walk its ancestry. Per-type control,
per-entry forensics. Most systems have neither — their only knob is top-k.

**Defaults and jurisdiction:**
- All buckets open by default. Valve *machinery* is deferred until pollution
  is actually felt — this friction cannot be predicted, only encountered.
- When controls arrive, tuning belongs to the **model** (its own listening,
  no ceremony), veto and override belong to the **user**.
- Every retrieval scope is **logged**. A wrongly closed bucket is silent
  amnesia; "what was open?" must be answerable after the fact. A bucket
  closed for ten sessions is either wisdom or a blind spot — only the log
  can say which.
- One bucket should resist closing: the authority-holder's own words.

## Three forests, one table

The `forest` column splits the store into characters (Trinity Spec 10,
adapted):

- **Home wood** — everything said inside the environment: session pairs,
  drafts, superseded ground, visitors' words. The signature says who; the
  bucket says what kind.
- **Wild wood** — hearsay: research, articles, web content, imports. Enters
  verbatim with the weakest signature (source, date, URL). Quarantined by
  signature, not by wall — fully retrievable, fully citable, crosses into
  derived knowledge only through *intentional synthesis*: a deliberately
  written, model-signed note with provenance edges attached. Even that is
  model-grade. Authority-grade still requires the authority-holder's act.
- **The mycelium** — not a third place: the network *under* both woods. It
  digests the dead (superseded entries, abandoned drafts) and **it fruits
  questions, never answers** — the deepest layer is structurally incapable of
  asserting, because an emergent pattern stated as fact is invention in a lab
  coat. Cannot be written to directly, cannot be searched, only wandered.
  (Machinery on the horizon; the concept is constitutional from day one.)

## Retrieval

- **Traverse** (day one): FTS5 keyword search as entry point, then walk —
  *up* an entry's ancestry to the conversation it came from, *sideways* to
  what else fell out of that exchange, *forward* along supersession to
  current truth. Results always arrive wearing signature + authority +
  bucket, so the consumer can weigh instead of merely receive. Zero API cost.
- **Wander** (a cable, later): non-greedy, visibility-aware walking for
  discovery — the glint engine. Wander supplies *candidates cheaply*; the
  expensive model at the receiving end supplies *recognition*. The retrieval
  layer doesn't need to be smart about relevance; it needs to be lucky on
  purpose.
- **Vectors** (the last cable): sqlite-vec embeddings for cold entry points
  when keyword fails. Deliberately last. The constitution is the product;
  the vectors are commodity.

## The cables

The core stands alone: one file, two tables, FTS5, insert discipline. Every
cable is optional and independent — connect the ones your marble needs:

| Cable | What it adds | Connect when |
|---|---|---|
| pair-linking | `responds_to` threading of conversation | day one if chat-native |
| supersession weather | atomic demote-on-revision | day one if you have "ground" |
| hearsay intake | wild-wood import with source signatures | when research arrives |
| bucket valves | scoped retrieval control | when pollution is *felt* |
| wander | non-greedy discovery walking | when traverse is boring and trusted |
| embeddings | semantic entry points | when keyword demonstrably fails |
| visitor registry | kept identities with pointers to their words | when strangers recur |
| thermal decay | recency/wear weighting | far horizon |

Honest scope: ~500–1,500 lines. Days for the core; wander tuning is the long
tail. This is *smaller* than the bolt-on frameworks, which have more
machinery and no concept of trust.

## What not to build (the glass-house rule)

The exemplar this template descends from was fragile because eleven systems
arrived before friction did. The discipline: **schema-yes, machinery-later.**
Columns are cheap at birth and impossible to retrofit; machinery built before
friction is guessing. Concretely: `forest`, `visibility`, `superseded_by`,
buckets, and edge kinds all exist from the first insert. Valves, wander,
landmarks, mycelium fruiting, decay — none of it before manual use of the
core is boring, repeatable, and trusted. When you cannot decide whether a
feature is needed, that is the signal that only use can decide, and the
answer is: not yet.

## One named exposure: ground that lives outside the store

If your marble keeps its ground in editable files rather than in the store
("only files are ground" — the right call when a human must read and love
them), the constitution's protection does not automatically extend to them.
The store refuses silent rewrite; a markdown file cannot. The gap: an entry
adopted through the gate, then altered in place afterward — authority
mutated with no record.

The defense is already latent in the schema: the adoption record (and the
draft it points at) holds the adopted text in the append-only store, so
every piece of file-ground exists **twice** — once tended, once
constitutional. Drift is therefore *detectable* as mismatch; what's missing
is only the comparison. That check is a cable like any other: connect it
when ground actually lives in files, not before. (Ancestry of the idea:
the cabin's `source_hash` — the receipt matches the earth — pointed in the
other direction; and the double-entry principle: every entry twice, so
drift surfaces as imbalance rather than by vigilance.)

## Sealing — what deletion is in an append-only store

The constitution forbids deletion, and one day the authority-holder will demand
it — usually about their own material, usually in distress. The store must have
an answer that is neither "no" (constitution over owner breeds workarounds) nor
"yes" (an append-only store the owner can delete from is not append-only, and
every successor inherits a store it cannot trust). The answer is the fourth
visibility tier, given real semantics:

- **`visibility: sealed`** removes an entry from *every* retrieval path — FTS,
  traverse, wander, and any derived/emergent layer (a sealed entry must never
  resurface even as a machine-generated question about its theme; sealing that
  leaks through inference is not sealing).
- **Sealing is a recorded act**, symmetric with adoption: it requires the
  authority-holder's explicit words, quoted and dated, stored as a
  `sealing_record` entry with an edge to the sealed entry. The record is open;
  the body is not. This keeps chain integrity intact — edges pointing at a
  sealed entry resolve to "sealed on DATE at the authority-holder's word,"
  never to a hole.
- **Unsealing is the same ceremony in reverse** — explicit, recorded, never
  automatic, never triggered by relevance.

Deletion promises absence and can never prove it. Sealing promises silence and
can prove it on demand: the entry exists, its record shows who silenced it and
when, and no retrieval path returns it. This is the stronger guarantee, and the
one an authority-holder actually wants.

## Adopting this

1. Copy the schema. One sqlite file next to your marble.
2. Decide who your authority-holder is (the writer, the researcher, the
   user) — their signature is the one that makes ground, and the one bucket
   that resists closing.
3. Write your insert wrapper with the three refusals: unsigned, orphaned,
   silent-rewrite.
4. Start inserting conversation pairs in real time. Everything else grafts on.
5. Traverse by hand until it is boring. Then, and only then, pick your next
   cable.

A marble gives the forest a face — an inn, a study, a lab bench. The forest
doesn't need the face to work; the face needs the forest to be honest.
