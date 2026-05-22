# 0026 - Production Web Image Build Configuration

## Status

Accepted on 2026-05-22.

## Context

Next.js inlines `NEXT_PUBLIC_*` environment variables into browser bundles during
`next build`. The web Dockerfile previously built with localhost and mock-Google
public defaults, which is convenient locally but unsafe for images published to
GHCR as production artifacts.

The official Next.js environment documentation confirms that public variables
are build-time browser bundle inputs. Server-only environment variables can still
be read at runtime during dynamic App Router rendering.

## Decision

The web Dockerfile now accepts explicit build arguments for browser-visible
values and defaults them to non-local production-safe placeholders. The build
stage runs with `ENV=production` and disables public mock Google affordances.
Runtime containers still receive real deployment configuration through
environment variables.

Docker Compose passes local development build arguments explicitly, including
the nginx origin and `NEXT_PUBLIC_USE_MOCK_GOOGLE=true`, so the containerized
dev contract keeps the same mock Google login affordances as hot-reload dev. The
login route is also rendered dynamically and checks the server environment for
mock Google availability, avoiding stale build-time UI when a deployment changes
provider mode.

The image publishing workflow also runs Compose e2e and README screenshot
verification before pushing GHCR images, so published images are gated by the
same full-stack behavior the README promises.

## Consequences

Published web images no longer bake `localhost` or public mock-mode flags into
the browser bundle. Deployments that need browser Sentry or other public values
must pass them as build arguments when building environment-specific images.

Compose development images intentionally bake local public values because they
are not the GHCR production artifacts and must satisfy the zero-key local login
contract.

Builds take longer because image publishing now waits for full-stack e2e and UI
screenshot verification.

## Alternatives considered

Keeping local defaults in the Dockerfile was rejected because GHCR images are
production artifacts. Moving public runtime configuration to a browser-fetched
config endpoint was rejected for now because current client code does not need a
runtime public API origin; browser API calls go through the same-origin
`/api/backend` proxy.
