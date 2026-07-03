#!/usr/bin/env node
/**
 * Pack-level arrival ref check — the check Cabin earned.
 *
 * Every backtick file/dir path in a specimen's arrival documents must resolve
 * on disk. An arrival seat pointing at missing paths is false ground at the door.
 *
 * Usage (repo root): node Reference/verify_arrival_refs.mjs
 */

import { existsSync, readdirSync, readFileSync } from "node:fs";
import path from "node:path";
import process from "node:process";
import { fileURLToPath } from "node:url";

const here = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(here, "..");
const examplesRoot = path.join(root, "EXAMPLEmarbles");

const ARRIVAL_DOCS = [
  "CLAUDE.md",
  "AGENTS.md",
  "ARRIVAL.md",
  "MANIFEST.md",
  "QUICKSTART.md",
];

// Repo-relative paths in backticks, e.g. `tools/lift-write.mjs` or `HANDOFF.md`.
const FILE_REF = /`([A-Za-z0-9_./\\-]+\.(?:md|py|mjs|sql|txt|json|jsonl|ps1))`/g;

// Directory buckets named in backticks, e.g. `ledger/` or `docs/letters/`.
const DIR_REF = /`([A-Za-z0-9_./\\-]+\/)`/g;

// Markdown links to local paths, e.g. [fix.py](lighthouse/fix.py).
const LINK_REF = /\[[^\]]*\]\(([^)#?][^)]*)\)/g;

// Paths outside the marble root — pack-level pointers, not door-map rot.
const OUTSIDE_MARBLE = /^(?:EXAMPLEmarbles\/|Manual\/|Reference\/|TestData\/|\.\.\/)/;

function listMarbles() {
  return readdirSync(examplesRoot, { withFileTypes: true })
    .filter((entry) => entry.isDirectory())
    .map((entry) => entry.name)
    .sort();
}

function collectRefs(text) {
  const refs = new Set();
  for (const re of [FILE_REF, DIR_REF, LINK_REF]) {
    re.lastIndex = 0;
    for (const match of text.matchAll(re)) {
      const ref = match[1].replace(/\\/g, "/");
      if (ref.startsWith("http://") || ref.startsWith("https://")) continue;
      if (OUTSIDE_MARBLE.test(ref)) continue;
      refs.add(ref);
    }
  }
  return [...refs];
}

function checkMarble(marbleName) {
  const marbleRoot = path.join(examplesRoot, marbleName);
  const problems = [];

  for (const docName of ARRIVAL_DOCS) {
    const docPath = path.join(marbleRoot, docName);
    if (!existsSync(docPath)) continue;

    const text = readFileSync(docPath, "utf8");
    for (const ref of collectRefs(text)) {
      const target = path.join(marbleRoot, ref);
      if (!existsSync(target)) {
        problems.push(`${marbleName}/${docName}: points to \`${ref}\` which does not exist`);
      }
    }
  }

  return problems;
}

function main() {
  const problems = [];
  for (const marble of listMarbles()) {
    problems.push(...checkMarble(marble));
  }

  if (problems.length === 0) {
    console.log(`PASS: arrival refs resolve for ${listMarbles().length} specimens.`);
    process.exit(0);
  }

  console.error("Arrival ref check failed:\n");
  for (const problem of problems) {
    console.error(`  ${problem}`);
  }
  process.exit(1);
}

main();
