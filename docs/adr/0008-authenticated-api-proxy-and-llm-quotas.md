# 0008 — Authenticated API Proxy And LLM Quotas

## Status

Accepted on 2026-05-21.

## Context

The API already validated Auth.js-issued JWTs, but browser-side client components were calling FastAPI directly. Because Auth.js cookies are HTTP-only, client-side mutations could not attach a bearer token without weakening cookie security. Rate limiting also existed only as route-level throttling, so LLM usage had no daily per-user ceiling.

## Decision

Browser mutations now call a same-origin Next.js `/api/backend/*` route. The proxy reads the active Auth.js session server-side, mints a five-minute RS256 API bearer, and forwards the request to FastAPI. FastAPI resolves that bearer into a `Principal`, maps it to the seeded or first-seen `User`, and records LLM token usage in `llm_usage_days` by UTC date.

LLM daily caps are configurable by plan: free users default to 50,000 tokens, paid users to 500,000 tokens, and admins are uncapped. If a user exhausts the cap, the API returns RFC 9457 Problem Details with `code: "quota_exceeded"`.

## Consequences

Client components never read or store auth tokens. API mutations can be rate-limited and quota-limited by user where a session exists, while anonymous-compatible routes continue to fall back to IP-based rate-limit keys.

Next.js needs an internal API base URL for server route handlers. Local development defaults to `http://localhost:8000/api/v1`; Compose sets `API_INTERNAL_URL=http://api:8000/api/v1`.

API bearer signing uses `AUTH_JWT_PRIVATE_KEY` in production. Development falls back to a process-global RSA key so separate Next.js dev route bundles can mint and verify the same short-lived bearer tokens without committing a private key. Auth.js session cookie encryption remains handled by Auth.js using `AUTH_SECRET`.

## Alternatives considered

Direct browser calls with a readable token endpoint were rejected because they would expose bearer tokens to client JavaScript. Making every mutation a Server Action was viable, but a narrow proxy keeps the existing client components and typed API helper intact while preserving the same security boundary.
