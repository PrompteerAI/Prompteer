# 0003 - Auth.js API Bearer Validation Through JWKS

## Status

Accepted on 2026-05-20.

## Context

The legacy backend issued and verified its own password-based JWTs. The rebuild uses the Next.js app as the SSO surface with Auth.js and Google OAuth.

## Decision

The web app keeps Auth.js sessions in Auth.js-managed encrypted JWT cookies. Browser code never reads those cookies or receives a reusable auth token. When a browser request reaches the same-origin `/api/backend/*` proxy, the Next.js server reads the active Auth.js session, mints a short-lived RS256 API bearer token, and exposes the corresponding public key at `/api/auth/jwks`. The FastAPI backend validates only those proxy-issued bearer tokens against that JWKS URL and treats Auth.js as the identity authority.

## Consequences

The backend avoids duplicating login flows and can rotate API bearer signing keys without sharing symmetric secrets with every service. Local development uses a dev-only keypair and mock Google OAuth when Google credentials are absent. Production can provide `AUTH_JWT_PRIVATE_KEY` and `AUTH_JWT_KEY_ID` to make API bearer key material stable across deploys. Auth.js session cookie encryption remains owned by Auth.js and `AUTH_SECRET`.

## Alternatives considered

Using the Auth.js session cookie itself as the FastAPI credential was rejected because it would couple backend validation to Auth.js cookie internals. HS256 shared API bearer secrets are simpler, but they make key rotation and service isolation weaker.
