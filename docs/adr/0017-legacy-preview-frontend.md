# 0017 — Legacy Preview Frontend

## Status

Accepted on 2026-05-21.

## Context

The original Prompteer frontend lived in a separate Vite/React repository and had a distinct white-header, blue-banner, card-heavy challenge UI. The rebuilt monorepo already has a production-oriented `apps/web` frontend, but the team also wants to compare the rebuilt product against a frontend that visually follows the old project.

## Decision

Add `apps/web-legacy` as a second Next.js app in the pnpm workspace. It recreates the old design language and route shapes while reading the rebuilt FastAPI APIs. Auth.js, JWKS, and API bearer-token minting remain owned by `apps/web`; the legacy preview proxies authenticated browser requests through the primary web app's `/api/backend/*` gateway instead of creating a second issuer.

## Consequences

`pnpm dev:legacy` starts the API, primary web app, and legacy preview together. The preview listens on `WEB_LEGACY_PORT` and expects the primary web app on `WEB_PORT`. Routes whose rebuilt backend endpoints do not exist yet keep legacy-shaped shells and state that authoritative data is pending rather than inventing fake data.

## Alternatives considered

Copying the old Vite app would preserve source-level similarity but would reintroduce the obsolete localStorage token model and stale API paths. Running a second Auth.js/JWKS issuer in `web-legacy` was rejected because it would split API trust and make running both frontend designs at once fragile.
