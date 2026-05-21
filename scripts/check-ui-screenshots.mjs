#!/usr/bin/env node
// Checks that README screenshot references are covered by generated verifier
// candidates and committed docs/screenshots assets.
import { createHash } from "node:crypto";
import { existsSync, readdirSync, readFileSync } from "node:fs";
import { basename, join } from "node:path";
import { spawnSync } from "node:child_process";

const readmePath = "README.md";
const docsDir = "docs/screenshots";
const candidateDirs = [
  ".verify/screenshots/readme",
  ".verify/screenshots/legacy",
];

function pngFilesIn(directory) {
  if (!existsSync(directory)) {
    return [];
  }
  return readdirSync(directory)
    .filter((name) => name.endsWith(".png"))
    .sort();
}

function readmeScreenshotNames() {
  const readme = readFileSync(readmePath, "utf8");
  return [
    ...new Set(
      [...readme.matchAll(/docs\/screenshots\/([^)\s]+\.png)/g)].map(
        (match) => match[1],
      ),
    ),
  ].sort();
}

function trackedScreenshotNames() {
  const result = spawnSync("git", ["ls-files", `${docsDir}/*.png`], {
    encoding: "utf8",
  });
  if (result.status !== 0) {
    throw new Error(result.stderr || "git ls-files failed");
  }
  return result.stdout
    .split("\n")
    .filter(Boolean)
    .map((path) => basename(path))
    .sort();
}

function generatedScreenshotNames() {
  return [
    ...new Set(candidateDirs.flatMap((directory) => pngFilesIn(directory))),
  ].sort();
}

function setDiff(left, right) {
  const rightSet = new Set(right);
  return left.filter((item) => !rightSet.has(item));
}

function hash(path) {
  return createHash("sha256").update(readFileSync(path)).digest("hex");
}

function candidatePathFor(name) {
  for (const directory of candidateDirs) {
    const path = join(directory, name);
    if (existsSync(path)) {
      return path;
    }
  }
  return null;
}

function assertSameSet(label, expected, actual, failures) {
  const missing = setDiff(expected, actual);
  const extra = setDiff(actual, expected);
  if (missing.length > 0 || extra.length > 0) {
    failures.push(
      `${label} mismatch: missing=[${missing.join(", ")}] extra=[${extra.join(", ")}]`,
    );
  }
}

const readmeNames = readmeScreenshotNames();
const trackedNames = trackedScreenshotNames();
const generatedNames = generatedScreenshotNames();
const failures = [];

assertSameSet(
  "tracked docs/screenshots vs README",
  readmeNames,
  trackedNames,
  failures,
);
assertSameSet(
  "generated verifier candidates vs README",
  readmeNames,
  generatedNames,
  failures,
);

const changed = [];
for (const name of readmeNames) {
  const docsPath = join(docsDir, name);
  const candidatePath = candidatePathFor(name);
  if (!candidatePath || !existsSync(docsPath)) {
    continue;
  }
  if (hash(docsPath) !== hash(candidatePath)) {
    changed.push(name);
  }
}

if (changed.length > 0) {
  failures.push(
    `README screenshot candidates differ from committed docs assets: ${changed.join(", ")}`,
  );
  failures.push(
    "Review .verify/screenshots/readme and .verify/screenshots/legacy, then run make update-ui-screenshots to promote approved images.",
  );
}

if (failures.length > 0) {
  console.error(failures.join("\n"));
  process.exit(1);
}

console.log(
  `Verified README screenshot coverage: ${readmeNames.length} referenced, ${trackedNames.length} tracked, ${generatedNames.length} generated.`,
);
