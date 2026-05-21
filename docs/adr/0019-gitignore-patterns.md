# 0019 - Gitignore Patterns

## Status

Accepted on 2026-05-22.

## Context

Prompteer is a public monorepo with Next.js, pnpm, Turborepo, Playwright, Vitest, FastAPI, uv, Alembic, Docker Compose, and local mock services. A single root `.gitignore` must keep generated output, secrets, dependency folders, local verification artifacts, and local-agent files out of the repository while preserving contributor-facing docs and curated screenshots.

## Decision

Maintain one root `.gitignore` built from current best-practice patterns for the tools in use, verified against official or primary references on 2026-05-22:

- Next.js project structure documents `.gitignore` as a standard root project file and the generated `.next` output remains untracked.
- Turborepo documents `.turbo` as cache output that should be ignored.
- pnpm's package layout centers dependency material under `node_modules`, which remains generated state.
- Playwright documents `test-results` as the default artifact output directory and `playwright-report` as the HTML report location.
- Vitest documents generated coverage reports, so `coverage/` remains ignored.
- GitHub's maintained Python `.gitignore` template covers Python caches, virtual environments, build outputs, coverage, and tool caches.
- uv uses local virtual environments and lockfiles; virtual environments are ignored while `uv.lock` stays tracked.

The repo also ignores `AGENTS.md`, `AGENTS.override.md`, `.codex/`, `.verify/`, `.mock/`, local environment files, editor noise, OS junk, logs, and local Compose overrides. `docs/screenshots/` is not ignored because curated README-grade screenshots are public documentation.

References checked:

- https://nextjs.org/docs/app/getting-started/project-structure
- https://turborepo.com/repo/docs/reference/run
- https://github.com/pnpm/pnpm
- https://playwright.dev/docs/test-cli
- https://vitest.dev/guide/coverage.html
- https://github.com/github/gitignore/blob/main/Python.gitignore
- https://docs.astral.sh/uv/

## Consequences

Generated dependency, build, test, cache, secret, verification, and mock-output files stay out of commits by default. Contributors can still add curated screenshots under `docs/screenshots/`, and Python/uv reproducibility is preserved by committing `uv.lock`.

Any future tool that writes generated state should update the root `.gitignore`, this ADR if the decision is architectural, and the verification list in the [ADR index](README.md).

## Verification

Run:

```bash
git check-ignore -v .env node_modules apps/web/.next apps/api/.venv
git check-ignore -v docs/screenshots/01-landing.png
```

The first command should print matching ignore rules for all four paths. The second command should print nothing and exit with status `1`, confirming curated screenshots are not ignored.

## Alternatives Considered

Per-directory `.gitignore` files would keep patterns closer to each app but make the public repo contract harder to audit. A generated `.gitignore` would reduce manual maintenance but obscure the explicit security and documentation choices this monorepo needs.
