# Prompteer

Prompteer is a prompt challenge and sharing platform rebuilt as a production-ready monorepo.

The target local contract is:

```sh
cp .env.example .env
docker compose up -d
pnpm dev
```

With no external API keys, the app uses deterministic local mocks for Google OAuth, LLM providers, Stripe, and SendGrid.

## Workspace

- `apps/web` - Next.js App Router frontend
- `apps/api` - FastAPI backend
- `packages/*` - shared TypeScript configuration and types
- `infra/*` - nginx, Postgres, and Compose support files
- `docs/*` - public architecture, ADRs, runbooks, screenshots, and integration notes

## Status

The rebuild is in progress. See `docs/architecture.md` and `docs/adr/` for accepted design decisions.

## Current Verified Slice

The current scaffold starts the FastAPI and Next.js development servers together:

```sh
cp .env.example .env
docker compose up -d
pnpm install
uv sync --project apps/api --dev
pnpm dev
```

Health checks:

- Web: `http://localhost:3000/api/health`
- API: `http://localhost:8000/api/v1/health/live`
- API readiness: `http://localhost:8000/api/v1/health/ready`

Seed demo data:

```sh
make seed
```

The seed command is idempotent and creates demo users, challenge categories, one public share, and one board post.

![Prompteer home screen](docs/screenshots/01-home.png)

## Verification

The scaffold currently passes:

```sh
pnpm lint
pnpm typecheck
pnpm test
cd apps/api && uv run ruff check .
cd apps/api && uv run ruff format --check .
cd apps/api && uv run mypy app tests
cd apps/api && uv run pytest
pnpm --filter @prompteer/web build
```
