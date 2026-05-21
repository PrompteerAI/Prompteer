#!/usr/bin/env node
// Verifies that project-owned environment variables read by runtime code,
// Compose, and local scripts are documented in the canonical .env.example.
import { readFileSync } from "node:fs";
import { spawnSync } from "node:child_process";

const ENV_EXAMPLE_PATH = ".env.example";

const SCAN_FILES = [
  "apps/api/app/core/config.py",
  "apps/web/src/lib/env.ts",
  "apps/web-legacy/src/lib/env.ts",
  "apps/web/src/instrumentation-client.ts",
  "apps/web/src/sentry.edge.config.ts",
  "apps/web/src/sentry.server.config.ts",
  "apps/web/next.config.ts",
  "apps/web/playwright.config.ts",
  "apps/api/scripts/start.sh",
  "apps/api/Dockerfile",
  "apps/web/Dockerfile",
  ".github/workflows/ci.yaml",
  ".github/workflows/build.yaml",
  ".github/workflows/e2e.yaml",
  "scripts/backup-db.sh",
  "scripts/bootstrap.sh",
  "scripts/check-compose-health.sh",
  "scripts/check-openapi-types.sh",
  "scripts/compose-up.sh",
  "scripts/dev.sh",
  "scripts/lib/load-env.sh",
  "scripts/reset-db.sh",
  "scripts/api-dev.sh",
  "scripts/api-test.sh",
  "scripts/web-dev.sh",
  "scripts/web-build.sh",
  "scripts/dev-legacy.sh",
  "scripts/web-legacy-dev.sh",
  "scripts/web-legacy-build.sh",
  "scripts/restore-db.sh",
  "scripts/verify-backup-restore.sh",
  "scripts/verify-ui.mjs",
  "compose.yaml",
  "package.json",
  "apps/web/package.json",
  "apps/web-legacy/package.json",
];

const SYSTEM_ENV_KEYS = new Set([
  "BASH_SOURCE",
  "CI",
  "FORCE_COLOR",
  "GITHUB_ENV",
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

function readText(path) {
  return readFileSync(path, "utf8");
}

function exampleKeys() {
  const keys = new Set();
  const duplicates = new Set();

  for (const line of readText(ENV_EXAMPLE_PATH).split("\n")) {
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

  if (!gitSucceeds(["check-ignore", "-q", ".env"])) {
    failures.push(
      ".env must be ignored so local credentials never get staged.",
    );
  }
  if (gitSucceeds(["check-ignore", "-q", ".env.example"])) {
    failures.push(".env.example must stay tracked and must not be ignored.");
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

  for (const path of SCAN_FILES) {
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
        `Duplicate keys in ${ENV_EXAMPLE_PATH}: ${[...duplicates].sort().join(", ")}`,
      );
    }
    if (missing.size > 0) {
      console.error(`Missing keys in ${ENV_EXAMPLE_PATH}:`);
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
    `${ENV_EXAMPLE_PATH} documents ${documented.size} environment variables; .env is ignored and .env.example is tracked.`,
  );
}

main();
