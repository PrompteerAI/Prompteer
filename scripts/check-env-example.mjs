#!/usr/bin/env node
// Verifies that project-owned environment variables read by runtime code,
// Compose, and local scripts are documented in the canonical .env.example.
import { readFileSync } from "node:fs";
import { spawnSync } from "node:child_process";

const envExamplePath = ".env.example";

const SCANNED_EXTENSIONS = new Set([
  ".js",
  ".json",
  ".mjs",
  ".py",
  ".sh",
  ".ts",
  ".tsx",
  ".yaml",
  ".yml",
]);

const SCANNED_FILENAMES = new Set([
  ".dockerignore",
  ".env.example",
  "Dockerfile",
  "Makefile",
  "compose.yaml",
  "package.json",
]);

const SCANNED_ROOT_PREFIXES = [
  ".github/workflows/",
  "apps/",
  "infra/",
  "packages/",
  "scripts/",
];

const IGNORED_SCAN_PATHS = [
  /^apps\/api\/uv\.lock$/,
  /^docs\//,
  /^packages\/shared-types\/src\/api\.ts$/,
  /^pnpm-lock\.yaml$/,
];

const SYSTEM_ENV_KEYS = new Set([
  "BASH_SOURCE",
  "CI",
  "FORCE_COLOR",
  "GITHUB_ENV",
  "GITHUB_OUTPUT",
  "GITHUB_REF_NAME",
  "GITHUB_REF_TYPE",
  "GITHUB_SHA",
  "GITHUB_STEP_SUMMARY",
  "HOSTNAME",
  "NEXT_RUNTIME",
  "NODE_ENV",
  "NO_COLOR",
  "PATH",
  "PWD",
  "BASE_SHA",
  "DEFAULT_DATABASE_URL",
  "HEAD_SHA",
  "SHORT_SHA",
]);

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

function filename(path) {
  return path.slice(path.lastIndexOf("/") + 1);
}

function shouldScan(path) {
  if (IGNORED_SCAN_PATHS.some((pattern) => pattern.test(path))) {
    return false;
  }
  if (
    !SCANNED_ROOT_PREFIXES.some((prefix) => path.startsWith(prefix)) &&
    !SCANNED_FILENAMES.has(path) &&
    !SCANNED_FILENAMES.has(filename(path))
  ) {
    return false;
  }
  return (
    SCANNED_EXTENSIONS.has(extension(path)) ||
    SCANNED_FILENAMES.has(path) ||
    SCANNED_FILENAMES.has(filename(path))
  );
}

function readText(path) {
  return readFileSync(path, "utf8");
}

function exampleKeys() {
  const keys = new Set();
  const duplicates = new Set();

  for (const line of readText(envExamplePath).split("\n")) {
    const match = /^([A-Z][A-Z0-9_]*)=/.exec(line);
    if (!match) {
      continue;
    }
    if (keys.has(match[1])) {
      duplicates.add(match[1]);
    }
    keys.add(match[1]);
  }

  return { keys, duplicates };
}

function collectMatches(source, regex) {
  const keys = new Set();
  for (const match of source.matchAll(regex)) {
    keys.add(match[1]);
  }
  return keys;
}

function referencedKeys(path) {
  const source = readText(path);
  const keys = new Set([
    ...collectMatches(source, /alias=["']([A-Z][A-Z0-9_]*)["']/g),
    ...collectMatches(source, /rawEnv\.([A-Z][A-Z0-9_]*)/g),
    ...collectMatches(source, /process\.env\.([A-Z][A-Z0-9_]*)/g),
    ...collectMatches(
      source,
      /(?<!\$)\$\{([A-Z][A-Z0-9_]*)(?::[-=?][^}]*)?\}/g,
    ),
    ...collectMatches(source, /(?<![\w$])\$([A-Z][A-Z0-9_]*)\b/g),
  ]);

  if (keys.has("")) {
    keys.delete("");
  }

  return [...keys].filter((key) => !SYSTEM_ENV_KEYS.has(key)).sort();
}

function gitSucceeds(args) {
  return spawnSync("git", args, { stdio: "ignore" }).status === 0;
}

function checkGitIgnoreContract() {
  const failures = [];
  const ignoredPaths = [
    [".env", ".env must be ignored so local credentials never get staged."],
    [
      ".env.local",
      ".env.local must be ignored so local credentials never get staged.",
    ],
    [
      ".env.production",
      ".env.production must be ignored so environment-specific secrets never get staged.",
    ],
    [
      "node_modules/",
      "node_modules must be ignored so installed dependencies never get staged.",
    ],
    [
      "apps/web/.next/",
      "apps/web/.next must be ignored so Next.js build output never gets staged.",
    ],
    [
      "apps/api/.venv/",
      "apps/api/.venv must be ignored so local Python virtualenvs never get staged.",
    ],
    [
      ".verify/",
      ".verify must be ignored so verification artifacts never get staged.",
    ],
    [
      ".mock/email",
      ".mock/email must be ignored so captured mock mail never gets staged.",
    ],
    [
      "AGENTS.md",
      "AGENTS.md must be ignored defensively because it is local agent context.",
    ],
    [
      ".codex/",
      ".codex must be ignored defensively because it is local agent config.",
    ],
  ];
  const allowedPaths = [
    [".env.example", ".env.example must stay tracked and must not be ignored."],
    [
      "docs/screenshots/01-landing.png",
      "docs/screenshots/01-landing.png must stay tracked and must not be ignored.",
    ],
  ];

  for (const [path, message] of ignoredPaths) {
    if (!gitSucceeds(["check-ignore", "--no-index", "-q", path])) {
      failures.push(message);
    }
  }

  for (const [path, message] of allowedPaths) {
    if (gitSucceeds(["check-ignore", "--no-index", "-q", path])) {
      failures.push(message);
    }
  }

  if (gitSucceeds(["ls-files", "--error-unmatch", ".env"])) {
    failures.push(".env must not be tracked.");
  }
  if (!gitSucceeds(["ls-files", "--error-unmatch", ".env.example"])) {
    failures.push(".env.example must be tracked.");
  }

  return failures;
}

function main() {
  const { keys: documented, duplicates } = exampleKeys();
  const missing = new Map();
  const gitIgnoreFailures = checkGitIgnoreContract();

  const scanFiles = gitLsFiles().filter(shouldScan);

  for (const path of scanFiles) {
    for (const key of referencedKeys(path)) {
      if (!documented.has(key)) {
        const paths = missing.get(key) ?? [];
        paths.push(path);
        missing.set(key, paths);
      }
    }
  }

  if (duplicates.size > 0 || missing.size > 0 || gitIgnoreFailures.length > 0) {
    if (duplicates.size > 0) {
      console.error(
        `Duplicate keys in ${envExamplePath}: ${[...duplicates].sort().join(", ")}`,
      );
    }
    if (missing.size > 0) {
      console.error(`Missing keys in ${envExamplePath}:`);
      for (const [key, paths] of [...missing.entries()].sort()) {
        console.error(`  - ${key} referenced by ${paths.join(", ")}`);
      }
    }
    for (const failure of gitIgnoreFailures) {
      console.error(failure);
    }
    process.exit(1);
  }

  console.log(
    `${envExamplePath} documents ${documented.size} environment variables; .env is ignored and .env.example is tracked.`,
  );
}

main();
