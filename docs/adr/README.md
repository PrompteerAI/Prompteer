# Architecture Decision Records

Prompteer uses ADRs to preserve the reasoning behind autonomous rebuild decisions. New ADRs should be short, dated, and linked from this index when they affect the public architecture, local development contract, security posture, or contributor workflow.

## Index

| Decision area                                                        | ADR                                                                                               |
| -------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------- |
| Monorepo structure, core stack, and shared toolchain                 | [0001 - Monorepo Stack](0001-monorepo-stack.md)                                                   |
| Mock-first provider architecture and zero-key local development      | [0002 - Mock-First External Integrations](0002-mock-first-integrations.md)                        |
| Auth.js as the identity authority and FastAPI JWKS validation        | [0003 - Auth.js JWT Validation Through JWKS](0003-auth-js-jwks-api-validation.md)                 |
| Local runtime startup model, now superseded by single-origin Compose | [0004 - Local Dev Runtime Contract](0004-local-dev-runtime-contract.md)                           |
| Rebuilt domain persistence model and Alembic-owned schema            | [0005 - Domain Schema Foundation](0005-domain-schema-foundation.md)                               |
| Local Google OIDC mock instead of browser-only fake login            | [0006 - Local Google OIDC Mock](0006-local-google-oidc-mock.md)                                   |
| Development-only startup migrations and idempotent seed data         | [0007 - Development Auto Bootstrap](0007-development-auto-bootstrap.md)                           |
| Same-origin authenticated API proxy and per-user LLM quotas          | [0008 - Authenticated API Proxy And LLM Quotas](0008-authenticated-api-proxy-and-llm-quotas.md)   |
| Production container hardening and worker health checks              | [0009 - Container Runtime Hardening](0009-container-runtime-hardening.md)                         |
| Compose serving the full app behind nginx on one local origin        | [0010 - Single Origin Compose Default](0010-single-origin-compose-default.md)                     |
| User-local date filters with UTC persistence                         | [0011 - User Local Date Filters](0011-user-local-date-filters.md)                                 |
| Hosted Stripe Checkout redirect contract                             | [0012 - Hosted Stripe Checkout URL](0012-hosted-stripe-checkout-url.md)                           |
| Generated locale manifest for add-a-file i18n expansion              | [0013 - Generated Locale Manifest](0013-generated-locale-manifest.md)                             |
| Real-provider readiness probes for external integrations             | [0014 - Real Provider Readiness Probes](0014-real-provider-readiness-probes.md)                   |
| Next.js 15 middleware compatibility bridge for `proxy.ts`            | [0015 - Next 15 Middleware Bridge](0015-next-15-middleware-bridge.md)                             |
| Runtime-generated signing key for the local Google OAuth mock        | [0016 - Runtime Google OAuth Mock Signing Key](0016-runtime-generated-google-oauth-key.md)        |
| Secondary legacy-style frontend preview over rebuilt APIs            | [0017 - Legacy Preview Frontend](0017-legacy-preview-frontend.md)                                 |
| Typed challenge media reference read contract                        | [0018 - Challenge Media Reference Read Contract](0018-challenge-media-reference-read-contract.md) |
| Root `.gitignore` provenance and verification contract               | [0019 - Gitignore Patterns](0019-gitignore-patterns.md)                                           |
| Dependabot tracking backend dependencies with uv                     | [0020 - Dependabot Uses The uv Ecosystem](0020-dependabot-uv-ecosystem.md)                        |
| FastAPI route, service, repository boundaries                        | [0021 - API Repository Boundaries](0021-api-repository-boundaries.md)                             |

## Gitignore Note

The root `.gitignore` is intentionally maintained as one repo-level file. It combines current best-practice ignore patterns for the toolchain Prompteer actually uses: Next.js, pnpm, Turborepo, Playwright, Vitest, Python/uv, Alembic, Docker Compose, local mock captures, and defensive local-agent files.

After changes to `.gitignore`, verify representative paths with `git check-ignore -v`:

- ignored: `.env`, `node_modules/`, `apps/web/.next/`, `apps/api/.venv/`
- tracked when present: `docs/screenshots/01-landing.png`

The rationale and source references are recorded in [0019 - Gitignore Patterns](0019-gitignore-patterns.md).
