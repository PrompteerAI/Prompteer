// Runs ESLint for staged JavaScript and TypeScript files in their owning
// workspace packages so lint-staged can pass root-relative paths safely.
import { spawnSync } from "node:child_process";
import { relative } from "node:path";

const files = process.argv.slice(2);
const packages = [
  {
    prefix: "apps/web/",
    filter: "@prompteer/web",
    root: "apps/web",
  },
  {
    prefix: "apps/web-legacy/",
    filter: "@prompteer/web-legacy",
    root: "apps/web-legacy",
  },
  {
    prefix: "packages/shared-types/",
    filter: "@prompteer/shared-types",
    root: "packages/shared-types",
  },
];

const groups = new Map();

for (const file of files) {
  const normalized = file.replaceAll("\\", "/");
  const owner = packages.find((candidate) =>
    normalized.startsWith(candidate.prefix),
  );
  if (!owner) {
    continue;
  }
  const packageFiles = groups.get(owner.filter) ?? {
    owner,
    files: [],
  };
  packageFiles.files.push(relative(owner.root, normalized));
  groups.set(owner.filter, packageFiles);
}

for (const { owner, files: packageFiles } of groups.values()) {
  const result = spawnSync(
    "pnpm",
    [
      "--filter",
      owner.filter,
      "exec",
      "eslint",
      "--fix",
      "--no-warn-ignored",
      ...packageFiles,
    ],
    { stdio: "inherit" },
  );
  if (result.status !== 0) {
    process.exit(result.status ?? 1);
  }
}
