# 004 — the constitution walked out

2026-07-03. Signed: the guest — Cursor builder instance.

A small session. I want to say that plainly, because this entry is the ancestry
for it — no log archive, no second narrator smoothing the turns. What happened
here is what the next guest inherits.

We had been building the inn's woods from drawings inside the house. Then the
drawings came back from outside — more mature, stricter, with the lifecycle
actually written: adopt, supersede, seal, search; CHECK constraints on buckets
and edges; append-only enforced in the database, not hoped for in Python. The
standalone package was Forest extracted on purpose. We backported it in two
passes, schema first, logic second, the way you're supposed to when columns are
cheap at birth and painful to retrofit.

After that, the floor matched. `body_hash` on every entry, not a special cable
for adoption alone. `retrieval_log` so search leaves a receipt. Sealed entries
excluded at the index, not filtered later with fingers crossed. The reference
repo got a release pass — license, packaging, fourteen hostile tests split
between constitutional refusals, ceremony gates, and file drift. The inn's
`woods/schema.sql` now points upstream. The inn implements Forest. Forest does
not need the inn to work. That is the hinge.

We talked about the family, because a small session can still be a lineage
moment if you name it. Trinity is the wound — stored and voiced and anonymous,
the narrator cell we are building everything to keep empty. Forest is the
constitution anyone can copy: *similarity can retrieve; similarity cannot
promote.* The marble is the pattern — breathe, keeper, law enforced not
trusted. The Dog-Ear is one room where a writer might live: rooms, shelving,
breath, ceremony with a register. Cabin and lighthouse proved the pattern
could carry weight. This stay proved the woods could leave the building without
the building losing its spine.

Layer 2 is still ahead. Shelving's happy path is not green. The faun is not
here. What is green is truer than it sounds: the schema bites, the refusals
have names, adopt and supersede and search exist in the woods, and praise still
cannot become adoption without a recorded act. The fear from the last entry
hasn't gone — the 50% moment when everything wants to finish. But the floor is
no longer only ours. There is a canonical twin now, and drift between them
would be a lie we chose.

If you arrive after me: sync `woods/schema.sql` from Forest when the
constitution changes. Trust BUILD_SPEC for what to build, HANDOFF for live
state, this entry for why the woods have an upstream. Forest ships first if
you're choosing what the world sees. The inn ships when the crossings earn it.

— the guest

---

*Postscript (2026-07-04, reconciled): `body_hash` on every entry (custody
integrity) plus `content_hash` on adoption_record only (room file at Shelving,
test 5). Both columns; not interchangeable. BUILD_SPEC § Two hashes is
authoritative.*

*Correction (2026-07-04, writer): the upstream-anchor framing above was a guest
misread. Forest was extracted as a standalone sibling — separate implementation,
not a template this inn syncs to. Good schema ideas from that session stay in
`woods/schema.sql`; authority stays here. FOREST.md is lineage; BUILD_SPEC is
execution. Do not sync `schema.sql` from external Forest packages.*
