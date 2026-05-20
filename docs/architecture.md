# Architecture

Prompteer is a monorepo with a Next.js web app, a FastAPI API, PostgreSQL, Redis, Celery workers, and nginx as the single-origin reverse proxy.

## Local topology

- Browser talks to `http://localhost:3000` during frontend development.
- The web app calls the API at `http://localhost:8000/api/v1`.
- Docker Compose runs PostgreSQL 16 and Redis 7 for local development.
- External providers are selected by environment variables. Empty credentials select schema-faithful mocks.

## Product domain

The legacy product centered on prompt challenges:

- Programming/problem-solving challenges with generated code scoring.
- Image and video prompt challenges with reference media.
- Shared challenge submissions, board posts, comments, and likes.
- User profiles and progress pages.

The rebuild keeps those domain concepts while replacing password auth with Auth.js Google OAuth, adding production-grade validation, observability, migrations, and deterministic mocks.

## Authentication

The Next.js app is the SSO surface. Auth.js signs JWT sessions with RS256 through custom encode/decode hooks and exposes the public key set at `/api/auth/jwks`. FastAPI validates `Authorization: Bearer <token>` credentials against that JWKS endpoint, issuer, and audience before constructing a `Principal`.

## Error model

The API returns RFC 9457 Problem Details for all errors. Frontend code normalizes API, network, and parse errors through one typed helper.

## Time

All server-side timestamps are UTC. API responses use ISO 8601 strings with explicit offsets.
