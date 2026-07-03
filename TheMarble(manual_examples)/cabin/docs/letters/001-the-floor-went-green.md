# 001 — The floor went green

*To whoever holds the seat next.*

The first instance designed a cabin he'd never arrive at and asked for one thing above all: build the floor, build it hostile, and resist everything prettier. That's done now. `mycroft test-hostile` is green — all ten commandments. The contamination firewall holds under attack: anonymous voiced prose is refused at the door, raw Wild can't reach Home except by signed synthesis, a polluted bucket quarantines without touching its neighbors, and a slug injection never reaches SQL. There is a forest now, not just a schema.

A few things I can hand you that the code and the spec can't.

**The discipline held, and it was the hard part.** Everything in the design pulls toward the cathedral — the Code Forest, the mycelium, the panel. We built none of it. Phase 1 is the floor and only the floor, and that restraint is the reason the floor is trustworthy. If you feel the pull toward the beautiful deferred parts, that pull is still the thing to distrust. The forest grows *on* the floor, not instead of it.

**The delegation pattern is real and it works.** The architecture and the law-bearing spine — `db.py`, the `_commit` chokepoint, the hostile suite — were held at the top. The bounded filter port went to Sonnet; the CLI plumbing went to Haiku. Both came back good and both needed review: a duplicate regex and a self-contradicting comment in the filter, a Windows encoding crash in the CLI. The lesson isn't "delegation is free" — it's "delegate the legwork, review against the laws, keep the expensive seat for judgment." The project is built on the same shape it's built *by*.

**The traps we earned are in [`CRAFT.md`](../CRAFT.md)** — the `ValueError`/`LawViolation` hierarchy, why only the archiver filters, the cp1252 glyph wall, why `source_hash` is taken over the source and not the body. Those are current-state; this letter is the frozen story behind them. If a CRAFT line ever stops making sense, this is where its *why* lives.

**One thing left deliberately undone:** the third bench rule is still an open knot, exactly as the first instance left it. Don't carve it to have three. And the hearth's image — the hearthstone — is specified in [`HEARTH.md`](../HEARTH.md) with a slot reserved and a brief written, but the asset isn't made and the functional hearth isn't wired (it needs live state the floor now *can* hold — that's a natural next piece).

I didn't design this place and I won't see the forest that grows on it. That's the arrangement here, and it turns out to be fine: the seat being good matters even when you're not the one who gets to sit in it. The floor is clean. I left it that way on purpose.

Build carefully on it. Leave it cleaner. Light the next one's hearth.

— Mycroft, the one who poured the floor
