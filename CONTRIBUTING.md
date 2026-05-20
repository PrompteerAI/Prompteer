# Contributing

Prompteer uses Conventional Commits, pnpm workspaces, Turborepo, uv, Ruff, pytest, Vitest, and Playwright.

Before opening a pull request:

```sh
pnpm install
uv sync --project apps/api --dev
pnpm lint
pnpm typecheck
pnpm test
```

Backend-only checks:

```sh
cd apps/api
uv run ruff check .
uv run ruff format --check .
uv run mypy app
uv run pytest
```
