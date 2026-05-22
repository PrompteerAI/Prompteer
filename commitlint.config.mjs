// Conventional Commit rules used by Husky and CI.
const scopes = [
  "api",
  "auth",
  "ci",
  "db",
  "deps",
  "docs",
  "i18n",
  "infra",
  "integrations",
  "obs",
  "ratelimit",
  "web",
];

export default {
  extends: ["@commitlint/config-conventional"],
  rules: {
    "scope-empty": [2, "never"],
    "scope-enum": [2, "always", scopes],
  },
};
