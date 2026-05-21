# 0007 - Development Auto Bootstrap

## Status

Accepted on 2026-05-21.

## Context

The local contract is `cp .env.example .env && docker compose up -d && pnpm dev`.
That flow should produce a usable demo app without requiring contributors to remember a separate migration or seed command.

Production still needs Alembic-owned schema changes and explicit operational control. The legacy backend created tables at application startup without that boundary, which is not acceptable for production.

## Decision

The FastAPI app now runs a development-only bootstrap during lifespan startup when `AUTO_SEED_ON_STARTUP=true` and `ENV` is not `production`.

The bootstrap:

- waits briefly for the local database to become reachable,
- runs `alembic upgrade head`,
- applies idempotent seed data,
- writes deterministic mock mailbox emails.

Production skips this path entirely. `make seed` remains available as an explicit rerun tool.

## Consequences

The default local command path creates demo users, challenges, board posts, shares, pre-completed mock Stripe checkouts for paid demo users, and mock emails automatically. Developers can still disable startup seeding with `AUTO_SEED_ON_STARTUP=false`.

The schema source of truth remains Alembic. Local startup invokes Alembic; it does not directly create tables from metadata outside the migration system.

## Alternatives Considered

Keeping `make seed` as a required manual step was simpler, but it violated the zero-extra-step local contract. Running `SQLModel.metadata.create_all()` directly on startup was also simpler, but it would blur the migration boundary the rebuild is trying to preserve.
