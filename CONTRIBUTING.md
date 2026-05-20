# Contributing

Thanks for improving Prompteer. This repository is a production-minded monorepo, so changes should be small, tested, and easy to review.

## Setup

Start with the README Quick Start, then install both toolchains:

```sh
pnpm install
uv sync --project apps/api --dev
cp .env.example .env
docker compose up -d
```

Run the app:

```sh
pnpm dev
```

## Branches And Commits

- Branch from `main`.
- Use Conventional Commits, for example `feat(api): add prompt quota checks`.
- Keep commits focused. Prefer several reviewable commits over one broad commit.
- Do not commit `.env`, local databases, mock captures, Playwright traces, or generated verification scratch files.

## Required Local Checks

Run these before opening a pull request:

```sh
pnpm lint
pnpm typecheck
pnpm test
pnpm build
cd apps/api && uv run ruff check .
cd apps/api && uv run ruff format --check .
cd apps/api && uv run mypy app tests
cd apps/api && uv run pytest
make types-check
```

Run Playwright when frontend behavior changes:

```sh
pnpm --filter @prompteer/web test:e2e
```

## Tests

- Backend tests live under `apps/api/tests`.
- Frontend unit tests use Vitest next to the relevant package or app code.
- End-to-end tests live under `apps/web/e2e`.
- Add tests at the same layer as the behavior you changed. API routes need route tests; browser workflows need Playwright coverage.

## Database Migrations

Use Alembic for schema changes:

```sh
cd apps/api
uv run alembic revision --autogenerate -m "describe change"
uv run alembic upgrade head
```

Production destructive changes must follow expand-contract:

1. Expand with the new shape.
2. Backfill data.
3. Cut reads and writes over.
4. Contract by removing the old shape after one release cycle.

Document exceptions in `docs/adr/`.

## API Types

After FastAPI route, schema, or response changes:

```sh
make types
make types-check
```

Commit both `docs/api/openapi-v1.json` and `packages/shared-types/src/api.ts`.

## External Integrations

Every integration needs:

- A real client selected by official env vars.
- A schema-faithful mock selected when credentials are blank.
- Tests for real-client request construction or mock behavior.
- A `docs/integrations/<provider>.md` page with sources and verified-on date.
- An ADR when the integration changes architecture, auth, billing, or data contracts.

## Code Review Expectations

Pull requests should explain:

- What changed and why.
- How the change was verified.
- Any migrations, environment variables, or operational steps.
- Screenshots for UI changes.
- ADR links for load-bearing decisions.

Reviewers should focus on correctness, security, regressions, observability, and missing tests before style preferences.

## Bugs And Feature Requests

Use GitHub Issues for public bugs and feature requests. Do not file security vulnerabilities publicly; use the process in [SECURITY.md](SECURITY.md).
