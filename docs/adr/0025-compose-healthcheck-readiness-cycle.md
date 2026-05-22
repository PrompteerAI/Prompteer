# 0025 - Compose Healthcheck Readiness Cycle

## Status

Accepted on 2026-05-22.

## Context

FastAPI readiness checks PostgreSQL, Redis, real or mock integrations, and the
Auth.js JWKS endpoint exposed by the Next.js web app. In Docker Compose, however,
the web container depends on the API container becoming healthy before nginx can
serve the full single-origin stack.

If the API container health check called `/api/v1/health/ready`, API health would
depend on web JWKS availability while web startup depends on API health. That
creates a Compose dependency cycle and can prevent a valid local stack from ever
starting.

## Decision

The API container health check uses `/api/v1/health/live` and
`/api/v1/health/startup`. This proves the process is responding and the database
schema is at the Alembic head before Compose starts dependent services.

The public nginx health check and CI still call `/api/v1/health/ready` after web
and nginx are running, so dependency reachability remains enforced for the full
stack.

## Consequences

Compose can bootstrap deterministically without weakening the externally visible
readiness contract. An API container can be marked healthy before Auth.js JWKS is
reachable, but nginx and CI catch that state before the stack is considered ready
for use.

Operators outside Compose should keep using `/api/v1/health/ready` for traffic
readiness and `/api/v1/health/startup` for migration drift.

## Alternatives considered

Calling readiness directly from the API container health check was rejected
because it forms the startup cycle. Removing JWKS from readiness was rejected
because it would hide an authentication dependency failure. Making web start
without waiting for API was rejected because local OAuth and API proxy routes
would race against API startup.
