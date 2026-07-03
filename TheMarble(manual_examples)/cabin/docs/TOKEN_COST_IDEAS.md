# TOKEN_COST_IDEAS — a living register (not gospel)

*A scratchpad, **not** the spec. `IMPLEMENTATION.md` is grounded and non-speculative on purpose — every mechanism there is proven. Speculation lives **here** instead, so it can't contaminate the spec. Add ideas as they come; an idea is **promoted** into the spec only once it's proven. This is the same firewall instinct the architecture runs on, turned on our own planning.*

> **Phase:** this is the **last** thing built — once the machine works. Aggressive token reduction everywhere possible, to make a $20 plan stretch far. It must **not** pull focus from the floor or the forest. Captured now only so the ideas survive.

**The thesis.** **The best context is context that stayed outside the model until it was needed.** The same law that protects the voice protects the bill: extract, log the rest, leave a pointer — a bulky thing enters context once (logged in full to the raw archive, §17), is replaced by a lean extract, and leaves a *scent* so the worker knows more exists and can reach for it. Nothing is destroyed; nothing resident is a brick.

**Status tags:** `[idea]` unproven · `[confirmed-pending-verify]` capability believed real, exact API unconfirmed · `[proven]` verified, ready to promote.

---

## Mode A — works inside Claude Code (no API key / own loop required)

These attack what *enters* context per call. They do **not** control Claude Code's own across-turn compaction (that's Mode B). Biggest sink they kill: a huge tool dump persisting in the window turn after turn.

- **`[confirmed-pending-verify]` PostToolUse output-rewrite — the automatic strip-and-log.**
  A `PostToolUse` hook reportedly returns `updatedToolOutput`, which *replaces* a tool's result before it reaches the model's context; `PreToolUse` reportedly returns `updatedInput` to modify a tool's arguments before it runs. Both said to work for built-in tools (Read/Bash/Grep/Edit).
  - **Design if it holds:** PostToolUse → write the **full** return to the raw archive (§17); return **extract + scent pointer** via `updatedToolOutput`. PreToolUse `updatedInput` → pre-shrink (inject a limit, scope a read).
  - **⚠ Verify before building:** the source confirming this had reliability tells (a non-working example, an implausibly long event list). Believe the **capability**; do **not** etch the field names `updatedToolOutput` / `updatedInput` into code until confirmed against the live Claude Code docs *or* a hands-on hook test. Build on the capability, not the remembered API surface.

- **`[idea]` Mycroft as the front door to expensive reads (the routed path).**
  Instead of `Bash(cat big_file)` / a broad `Read`, call `mycroft.read(path, query)`: it logs the full contents to the raw archive and returns only the query-relevant spans + a scent pointer. Needs **no** special Claude Code capability — Mycroft owns its own tool's return. Works even if the PostToolUse path above doesn't pan out. Query-scoped extraction also drops far less of what *this task* needs than a blind strip.

- **`[idea]` Quiet wrappers — the certain form of the front door. SHIP THESE FIRST.**
  CLI wrappers that default to low-output: `mycroft test` (pass/fail + first relevant failure, full log behind a handle), `mycroft rg` (capped, grouped by file, handles), `mycroft diff` (diffstat + changed symbols, full diff on request), `mycroft logs` (errors/warnings first, tail). **Sequencing note:** these need *no* hook capability — Mycroft owns the return — so they are guaranteed to work, unlike the PostToolUse sieve. Build the wrappers first; let the hook sieve be an *automatic upgrade* that covers the built-in tools once `updatedToolOutput` is verified. Certain-before-unverified.

- **`[idea]` Handle-first recall — compress retrieval, not just tool output.**
  `recall()` should return **handles** (bucket, one-line label, score) first, not bodies — open a body only on demand (`mycroft.open(n)`). Refines the current collector (which returns bodies). Obeys the surfacing discipline: relevance is scent, memory never talks over the human. A real improvement to bake into the collector, not just an economy add-on.

- **`[idea]` Scent pointers everywhere — extraction must be non-destructive AND self-announcing.**
  The danger is never dropping; it's *silent* dropping (you can't forage what you don't know exists). Every strip leaves `[full: N tok → archive:id; showing X of Y]`. Converts silent forgetting into visible, recoverable compression. This is the seam-audit principle (§10) applied to tool returns.

- **`[idea]` State-gauge-driven proactive clearing.**
  When the gauge shows the window filling, clear/condense sooner rather than riding a bloated context. (Depends on how much context-fullness visibility Mode A actually gets — easier in Mode B.)

- **`[idea]` Subagent offload for verbose operations.**
  Push noisy, high-token operations into an isolated subagent context; only the distilled result returns to the main window. Already a usable pattern; note it as a deliberate token lever.

- **`[idea]` Lean returns + dedup are already floor behavior.**
  Mycroft's own tools already return trimmed results, and `_commit` dedups near-identical writes (≥0.9 cosine). Keep every Mycroft tool's return lean by default — the cheapest token is the one never sent.

## Mode B — requires owning the API loop (own key / billing)

The biggest levers, unavailable as an MCP add-on. Here Mycroft builds the `messages` array and calls the model directly.

- **`[idea]` Frozen-prefix cache (the cache dividend, §9/§19).**
  *Reconcile reality to the cache, not the cache to reality.* One 1-hour cache write, then never refreshed within the hour; express change as appended deltas at the tail, never by rewriting the prefix. The single biggest cost lever — and only available in the standalone harness.

- **`[idea]` Full history intercept + clean (the standalone move).**
  Own `self.history`/`messages`: send a cleaned, extracted version each turn instead of the raw brick. Total control of what reaches the wire. Requires Mode B.

## Economy register, renders, and gates (output & interaction)

A different axis from Mode A/B (which control *input* context): this is about the worker's *output* and the *interaction*. Mostly instruction-layer — fine here, because it's low-stakes output style, but weaker than structure (see caution 4).

- **`[idea]` Economy modes — `mycroft economy {normal|compact|ledger|deep|off}`.**
  `compact` is the Mycroft default: concise but complete, no filler, no cheerleading, no restating the request — `Finding / Evidence / Patch / Test / Risk / Next`. `ledger` is terse packets for long implementation runs. **`deep` is preserved for design, audit, tradeoff, and spec writing** — this is what protects the authored voice (the letters, CRAFT, rationale) from caveman-corrosion. The rule: *spend words only when they reduce future turns.* Economy is total-work reduction, not silence — sometimes a longer answer is cheaper because it prevents a confused next turn.

- **`[idea]` Compact renders — a view, NEVER ground (hard invariant).**
  `MYCROFT.compact.md`, `CLAUDE.compact.md`, etc.: generated short renders of source docs, for startup economy. Each carries source path + source hash + render timestamp + mode. **Invariant, not guideline:** a compact render may *never* be embedded into a forest table or foraged as memory. One-line test — *does it enter a vec table?* If yes, it is the narrator (stored + voiced + generated). It is a regenerable cache beside the source, hash-checked for staleness; if it can ever reach Home, the design is wrong. This is the single piece of this whole register closest to the forbidden cell — wall it absolutely.

- **`[idea]` Economy stats — `mycroft economy stats`.**
  Product-shaped, legible to a $20-plan user: tool output archived behind handles vs. digest shown, estimated output tokens saved, biggest leak avoided this session, times Mycroft asked before thrashing (wired to bench rule 2).

- **`[idea]` Spend gates — pause before asymmetric-cost actions.**
  Trigger *only* when cost is likely lopsided (a broad scan, a command that may dump huge output): offer the quiet wrapper / targeted path instead. Not permission-for-everything; the bench-rule-2 cost asymmetry made interactive.

---

## Standing cautions (read before promoting any idea)

1. **Under-extraction is the real failure** — "knew it in the turn, lost it after." Every strip must be **non-destructive** (raw archive) and **self-announcing** (scent pointer). Aggressive on tokens, conservative on certainty: when in doubt, keep the span and always leave the pointer.
2. **Verify Claude Code capabilities before building on them** — especially anything remembered from a single source. Capability first, exact API confirmed second. (See the quiet wrappers: certain-before-unverified.)
3. **This phase is last.** Don't let a token-saving idea become a reason to build ahead of the floor and the forest.
4. **Structure over instruction.** Where a saving can be made *structural* (the tool returns handles; the sieve strips at the door), do that — it can't be ignored. Reserve instruction (economy register, reciting a ladder) for low-stakes output style only; never lean on it for anything load-bearing.
5. **Compact renders may never become ground.** Restated because it is the one idea here that, done wrong, *is* the forbidden cell. A render is a disposable view, hash-checked against source; it never enters a forest table.
