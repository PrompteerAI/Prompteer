# 0015 - Next 15 Middleware Bridge

## Status

Accepted on 2026-05-21.

## Context

The target layout names `apps/web/src/proxy.ts` as the App Router proxy entry.
That matches the Next.js 16 naming direction, but the current project is pinned
to Next.js 15.5.x. In this installed version, production builds discover
`middleware.ts`; relying only on `proxy.ts` leaves locale routing and
signed-out protected-route callback preservation inactive at runtime.

This was caught during Docker Compose browser verification: `/en/board`
redirected to `/en/login` without `callbackUrl`, and `/api/health` was
temporarily routed through locale middleware when the compatibility export did
not declare a static matcher in the discovered file.

## Decision

Keep the canonical implementation in `apps/web/src/proxy.ts`, and add
`apps/web/src/middleware.ts` as a small compatibility bridge for Next.js 15. The
bridge re-exports the proxy implementation and declares the same static matcher
locally so API, dev, Next internals, and static asset paths remain excluded.

## Consequences

Protected route redirects preserve the originally requested path in the current
Next.js version, while the codebase can remove `middleware.ts` after upgrading to
Next.js 16 and keep `proxy.ts` as the single entry point.

The bridge is intentionally thin: all behavior lives in `proxy.ts`, so tests and
future maintenance do not split routing logic across two files.

## Alternatives considered

Moving all logic back to `middleware.ts` would match Next.js 15 but drift from
the target structure. Waiting for a Next.js 16 upgrade before preserving
callback URLs would leave a user-visible navigation bug in the current runtime.
