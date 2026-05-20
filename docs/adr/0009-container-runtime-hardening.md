# 0009 - Container Runtime Hardening

## Status

Accepted on 2026-05-21.

## Context

Prompteer ships FastAPI, Celery, and Next.js as production containers. The rebuild requires multi-stage images, digest-pinned production bases, non-root runtimes, one process per container, and Docker health checks. The worker uses the same API image, so it cannot inherit a FastAPI HTTP health check without becoming unhealthy.

## Decision

Use digest-pinned `node:22-alpine` and `python:3.12-slim` bases for production images. The web image builds a Next.js standalone bundle and runs it as the bundled `node` user. The API image builds dependencies with uv in a builder stage, copies only the virtual environment and app source into the runtime stage, and runs as an unprivileged `prompteer` user. The FastAPI image keeps an HTTP liveness `HEALTHCHECK`; Compose overrides the inherited worker check with a Celery ping health check.

## Consequences

Runtime images no longer need package managers for normal operation. Base image updates require digest refreshes, and the worker health check must stay aligned with the Celery app name. Local Docker verification still depends on Docker being available on the host.

## Alternatives considered

Keeping uv in the runtime image was simpler, but it left extra tooling in production. Disabling the worker health check avoided false failures, but it would not satisfy the local Compose health expectations.
