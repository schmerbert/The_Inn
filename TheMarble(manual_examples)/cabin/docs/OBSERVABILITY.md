# OBSERVABILITY — trust as a checkable thing (a living register, not gospel)

*A scratchpad, **not** the spec — sibling of [`TOKEN_COST_IDEAS.md`](./TOKEN_COST_IDEAS.md) and [`MINIMALITY.md`](./MINIMALITY.md). Deferred. But it is the pillar that makes the rigor **visible**, so it is captured carefully.*

> **Phase:** deferred (the rendered panel is `IMPLEMENTATION.md` §21, built last). Captured now because "build for trust and legitimacy" is a first-class goal, not a finishing polish.

---

## The bar

Build for trust and legitimacy, measured concretely: someone calls this "vibecoded slop" in a thread before reading it. The goal is to **earn defenders and arm them** — people who look into it, come away believing, and can answer the dismissal with things anyone can *check*, not "trust me." A defender who says "it's good, honestly" is weak and loses the thread; a defender who says *"run `mycroft test-hostile`, read `_commit`, look at the refusal ledger"* is unanswerable. Claims are cheap. This project hands its advocates real ammunition — and prints its honest limits next to its wins, because a defender who already conceded the edges can't be ambushed by them.

The repo already does this for the *code* — AI-legible-first, laws visible at the enforcement site, a hostile test suite, limitations stated up front. Observability extends it to *runtime*: the system shows its work as it runs.

## The principle: logs obey LAW I

**Render the events; never narrate them.** `23:14 refuse mark→personal (no source-grip)` is *extraction* — the event exactly as it happened. "the system seemed to struggle with validation" is the **narrator**. Even the human-facing log is extraction, not summary. The same law that keeps memory clean keeps the logs honest — and is the reason they can be *legible* instead of the usual nightmare. A log that cannot drift cannot lie to you.

## Two layers (the §17 split, applied to logs)

- **Raw operational log** — cold, append-only JSONL, full fidelity, forensic. Not read by eye normally; machine-queryable. Nothing is ever lost.
- **The legible ledger** — curated, typed, leveled. What a human reads. Nesting-doll depth: a quiet headline by default, drill down to full provenance on demand (reach, not receive — the log never floods you).

## Typed events (a closed vocabulary → clean rendering)

`write` (extract/mark/synthesize/archive) · `refuse` (law violation) · `collect` · `quarantine`/`enable` · `dedup`. Each renders to **one legible line**, provenance available on drill-down. Because the vocabulary is the same closed set the laws already enforce, the renderer stays simple and the output stays uniform — there is no freeform text to wrangle. The structure that makes the *memory* clean makes the *log* clean for free.

## Refusals are the trust artifact

The single most legitimizing thing you can show is the firewall working, in the open.

- `mycroft test-hostile` green is the **static** proof — the laws hold under attack, once.
- The **refusal ledger** is the **living** proof — they keep holding in real use: every illegal write turned away, which law, why. A skeptic can watch the door refuse the narrator in real time.

Most systems hide their rejections in stack traces. Here, the rejection *is the product working*, so it is a first-class, readable event.

## Benchmarks (product-shaped, real, reproducible)

- **Performance:** embed latency, query latency, db size, entries per bucket.
- **Health:** dedup rate, refusal rate + *which* laws trip, quarantine events.
- **Economy:** raw archived vs. digest shown, tokens saved by handles (ties to [`TOKEN_COST_IDEAS.md`](./TOKEN_COST_IDEAS.md)).

**Discipline:** numbers are real and **reproducible** — a `mycroft bench` anyone can run on their own machine and get the same shape. A benchmark you cannot reproduce is marketing; this is not that.

## The anti-slop stack — what a skeptic can actually check

Laid out so the dismissal costs the skeptic, not the project:

1. **Tests that prove the hard claim** — the hostile suite refuses the *crimes*, not the happy path.
2. **One auditable door** — every write goes through `_commit`; the laws live in one readable place.
3. **Traceable provenance** — every stored thing carries writer / source / hash / lens / time, append-only.
4. **A legible operational log** — the laws visibly keep holding.
5. **Reproducible benchmarks** — real numbers anyone can regenerate.
6. **Limitations stated up front** (`IMPLEMENTATION.md` §19) — slop hides its edges; this names them. Honesty about what it *can't* do is itself a trust signal.

The "wow" is not polish. It is that **every claim is checkable, and the honest limits are printed next to the wins.**

## Near-free now vs. later

- **Near-free now:** the floor already writes structured rows with full provenance, so `mycroft log` (render recent writes/refusals legibly) and `mycroft stats` / `mycroft bench` are *small* — the data is already shaped right.
- **Later:** the dedicated operational event stream (collects/refusals as their own log, not inferred from rows) and the rendered panel (§21, last).

## Standing cautions

1. **The log is extraction, never summary** — if a line ever describes or interprets rather than records, it has become the narrator; cut it.
2. **Reproducible or it doesn't count** — a number a reader can't regenerate is marketing, and marketing is what "slop" means.
3. **Deferred.** Don't build ahead of the floor and the forest — but note this is one of the cheapest high-trust wins available when the time comes, precisely because the data is already structured.
