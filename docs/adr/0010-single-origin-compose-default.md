# 0010 - Single Origin Compose Default

## Status

Accepted on 2026-05-21.

## Context

The local contract has two needs that are easy to put in conflict: `docker compose up -d` should expose a working app at `http://localhost`, and `pnpm dev` should still be able to bind hot-reload web/API ports, defaulting to `3000` and `8000`. Mock Google OAuth also needs a browser-reachable authorization URL and container-internal token, userinfo, and JWKS URLs.

## Decision

Make the root Compose file start the full stack by default behind nginx on `HTTP_PORT`, defaulting to port 80. The web and API containers stay on the Compose network only, so local dev servers can still use `WEB_PORT` and `API_PORT`. PostgreSQL and Redis publish through `POSTGRES_PORT` and `REDIS_PORT` for local tools and tests. The mock Google issuer remains the public single-origin URL while discovery can publish internal server-to-server endpoints for Auth.js token exchange and userinfo/JWKS calls.

## Consequences

A fresh `docker compose up -d` can serve the containerized app at `http://localhost`. Developers who want only PostgreSQL and Redis can start those services explicitly. The OIDC mock now has separate public issuer and internal endpoint settings, and nginx must continue routing the public mock authorization path to FastAPI.

## Alternatives considered

Keeping the app behind an optional Compose profile avoided background app containers during local development, but it failed the single-command containerized app contract. Publishing API/web host ports from Compose would have been simpler, but it would collide with `pnpm dev`.
