# 0001 - Monorepo Stack

## Status

Accepted on 2026-05-20.

## Context

The legacy Prompteer code lived in separate frontend and backend repositories. The frontend used Vite and JSX. The backend used FastAPI but lacked the production scaffolding needed for migrations, background work, observable errors, and deterministic external-service mocks.

## Decision

Prompteer is rebuilt as a single monorepo with Next.js App Router, TypeScript, Tailwind CSS, Auth.js, FastAPI, SQLModel, Alembic, Celery, PostgreSQL, Redis, nginx, pnpm workspaces, uv, and Turborepo.

## Consequences

The repository has one root setup path and one root CI surface. JavaScript and Python tooling remain native to their ecosystems, with `Makefile` targets as the common entrypoint.

## Alternatives Considered

Keeping the split repositories would preserve history boundaries but make the local zero-key contract, CI, shared docs, and generated API types harder to keep coherent.
