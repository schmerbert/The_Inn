# MINIMALITY — a living register (not gospel)

*A scratchpad, **not** the spec — the sibling of [`TOKEN_COST_IDEAS.md`](./TOKEN_COST_IDEAS.md). Speculation lives here so it can't contaminate `IMPLEMENTATION.md`. Promote an idea into the spec only once it's proven.*

> **Phase:** deferred. The full power of everything here depends on the **concept-index** (the Code Forest, `IMPLEMENTATION.md` §20), which is a late build. Captured now so it survives.

**The idea, in our register.** Not "be lazy" and not a personality — the worker's discipline of *judgment before action*: **before writing code, decide whether the code should exist.** A careful forester/staff engineer who spends as little code as possible while preserving source-grip and correctness.

**The principle that makes it real, not a vibe:** *lazy about the solution, never about reading.* A recited ladder is instruction and can be ignored; this only becomes load-bearing when it is **backed by retrieval** — the worker actually checks what exists. That is the whole reason it belongs in *Mycroft* and not in a prompt: the project's memory of itself is what turns "don't rebuild what exists" from a slogan into something enforceable. (Structure over instruction — same caution as the token register.)

**Status tags:** `[idea]` unproven · `[idea, needs concept-index]` blocked on §20 · `[proven]`.

---

## `mycroft minimality` — the minimality gate (pre-code audit)

`[idea, needs concept-index]` Runs before edits, especially when the task smells like new architecture, new abstractions, new dependencies, new files, or a refactor. The ladder:

1. Does this need to exist at all? Is the requirement speculative?
2. Does this repo already do it?
3. Is there an existing helper, type, module, pattern, script, or command?
4. Does stdlib cover it? The platform natively? An already-installed dependency?
5. Can the fix live at the **shared root cause** instead of every caller?
6. Can it be a smaller patch?
7. Only then: the minimum new code that works.

**Backed by tools, not vibes** (this is the load-bearing part):
- before a new function → search the **concept-index**;
- before a dependency → check the package files;
- before a new abstraction → inspect existing call sites;
- before fixing one path → grep the sibling callers;
- before a feature → ask whether a config, DB constraint, CLI flag, existing API, or native behavior already solves it.

**Honest dependency:** until the concept-index exists, the gate degrades to *disciplined grep + package-file checks* (available now, still useful). Don't oversell a day-one gate as more than that. Output is compact (`Need exists / existing pattern / root-fix location / new dependency / patch shape`). If the answer is "do nothing," say so plainly.

## `mycroft minimality review` — the delete-list / overbuild audit

`[idea]` Reviews a diff for overbuilding. Returns **Delete** (duplicate of X, one-caller abstraction, stdlib already covers it, dependency used for 4 lines, future-proofing with no present caller, a refactor replacing a working system instead of repairing the seam) / **Keep** (root-cause fix, boundary test) / **Risk** (caller not checked, migration unclear). This is the direct answer to the recurring damage — things fade into the walls, working systems get reimplemented, functions get half-replaced. Make rebuilding harder than reusing.

## `shortcut_ledger` — sourced debt, thrift without amnesia

`[idea]` When the worker deliberately takes the smaller safe patch over the grand cleanup, record the deferred cleanup so "later" doesn't become vapor — **lawfully**:

- A deferred shortcut is a **`mark`** (authored), not an extraction.
- It needs **source-grip**: file path, symbol, reason, timestamp, source hash.
- It lives in a `debt` (or `rationale`) bucket — **never `project`**, never auto-ingested into Home.
- It surfaces only when relevant; it is dismissible or promotable.

This maps cleanly onto the existing `mark` writer + a new voiced bucket; it touches no law. Format: *chose local guard over full parser rewrite · reason: prod bug, root cause isolated · deferred: parser normalization · source: src/parser#normalizeInput hash:…*

---

## Naming & standing cautions

- **`mycroft minimality`**, not "ponytail" — the goal is to avoid code that should never exist, not laziness. No costume, no gimmick, no fake personality. A worker who looks before building.
- **Structure over instruction:** the gate is only as strong as its retrieval backing. The ladder alone is a prompt an agent can recite and ignore; the *tool calls* (concept-index, grep, package files) are what bind it.
- **Deferred, and behind the concept-index.** Do not build this ahead of the floor and the forest.
