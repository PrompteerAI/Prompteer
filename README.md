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
