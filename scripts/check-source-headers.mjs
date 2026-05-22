#!/usr/bin/env node
// Verifies tracked source files start with a short purpose header.
import { readFileSync } from "node:fs";
import { spawnSync } from "node:child_process";

const SOURCE_EXTENSIONS = new Set([
  ".css",
  ".js",
  ".mjs",
  ".py",
  ".sh",
  ".ts",
  ".tsx",
]);

const EXTRA_SOURCE_FILES = new Set([".husky/pre-commit", ".husky/commit-msg"]);

const EXCLUDED_PATHS = [
  /^\.husky\/_\//,
  /^apps\/web(?:-legacy)?\/src\/i18n\/locales\.generated\.ts$/,
  /^packages\/shared-types\/src\/api\.ts$/,
];

function gitLsFiles() {
  const result = spawnSync("git", ["ls-files"], {
    encoding: "utf8",
    stdio: ["ignore", "pipe", "pipe"],
  });
  if (result.status !== 0) {
    throw new Error(result.stderr || "git ls-files failed");
  }
  return result.stdout.split("\n").filter(Boolean);
}

function extension(path) {
  const index = path.lastIndexOf(".");
  return index === -1 ? "" : path.slice(index);
}

function isSource(path) {
  if (EXTRA_SOURCE_FILES.has(path)) {
    return true;
  }
  if (EXCLUDED_PATHS.some((pattern) => pattern.test(path))) {
    return false;
  }
  return SOURCE_EXTENSIONS.has(extension(path));
}

function isHeaderLine(line) {
  const trimmed = line.trim();
  return (
    trimmed.startsWith("//") ||
    trimmed.startsWith("/*") ||
    trimmed.startsWith("*") ||
    trimmed.startsWith("#") ||
    trimmed.startsWith('"""') ||
    trimmed.startsWith("'''")
  );
}

function isDirective(line) {
  const trimmed = line.trim();
  return /^["']use (client|server)["'];?$/.test(trimmed);
}

function firstMeaningfulLine(path) {
  const lines = readFileSync(path, "utf8").split(/\r?\n/);
  let index = 0;
  if (lines[index]?.startsWith("#!")) {
    index += 1;
  }
  while (index < lines.length && lines[index].trim() === "") {
    index += 1;
  }
  if (isDirective(lines[index] ?? "")) {
    index += 1;
    while (index < lines.length && lines[index].trim() === "") {
      index += 1;
    }
  }
  return lines[index]?.trim() ?? "";
}

function main() {
  const missing = [];
  for (const path of gitLsFiles().filter(isSource)) {
    const line = firstMeaningfulLine(path);
    if (!line || !isHeaderLine(line)) {
      missing.push(`${path}: ${line.slice(0, 100)}`);
    }
  }

  if (missing.length > 0) {
    console.error("Source files missing purpose headers:");
    for (const item of missing) {
      console.error(`  - ${item}`);
    }
    process.exit(1);
  }

  console.log("Verified tracked source file purpose headers.");
}

main();
