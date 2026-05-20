# 0004 - Local Dev Runtime Contract

## Status

Accepted on 2026-05-20.

## Context

The rebuild contract says a contributor should be able to copy `.env.example`, start Compose, and run `pnpm dev` to get a usable local system. The monorepo uses native tooling for both ecosystems: pnpm for the Next.js app and uv for the FastAPI app.

## Decision

`docker compose up -d` starts local infrastructure dependencies such as PostgreSQL and Redis. `pnpm dev` starts both application processes: FastAPI on port 8000 and Next.js on port 3000.

The root script uses a small shell wrapper instead of adding another JavaScript process manager dependency.

## Consequences

Local development has one command for application servers while keeping backend dependency management in uv. The script is Unix-shell oriented, which matches the current WSL development environment; if Windows-native support becomes a requirement, replace the shell wrapper with a cross-platform runner.

## Alternatives Considered

Running only Next.js from `pnpm dev` would be simpler, but it would violate the local zero-key end-to-end contract. Adding `concurrently` would be portable but unnecessary at this stage.
