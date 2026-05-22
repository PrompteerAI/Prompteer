# 0021 - API Repository Boundaries

## Status

Accepted on 2026-05-22.

## Context

The rebuild started with several FastAPI route modules and shared services
performing SQLModel reads or writes directly. That kept the first vertical
slice small, but it blurred the intended route, service, repository, and schema
boundaries documented for the monorepo.

## Decision

Add `app/repositories/` modules for users, challenges, community board reads,
LLM usage, and billing records. Routes now delegate user-visible workflows to
services, and services call repositories for persistence concerns.

## Consequences

Persistence details such as SQLModel queries, dialect-specific upserts, and
checkout/webhook row mapping are isolated from route handlers. Future route
changes should add service methods first and keep direct SQLModel access inside
repositories.

## Alternatives Considered

Leaving the route-level persistence in place would be simpler in the short
term, but it would keep growing API handlers into mixed transport, business,
and storage modules.
