# 0003 - Auth.js JWT Validation Through JWKS

## Status

Accepted on 2026-05-20.

## Context

The legacy backend issued and verified its own password-based JWTs. The rebuild uses the Next.js app as the SSO surface with Auth.js and Google OAuth.

## Decision

The web app signs session/API tokens with RS256 through Auth.js's custom JWT `encode`/`decode` hooks and exposes public keys at `/api/auth/jwks`. The FastAPI backend validates bearer tokens against that JWKS URL and treats Auth.js as the identity authority.

## Consequences

The backend avoids duplicating login flows and can rotate signing keys without sharing symmetric secrets with every service. Local development uses a dev-only keypair and mock Google OAuth when Google credentials are absent. Production can provide `AUTH_JWT_PRIVATE_KEY` and `AUTH_JWT_KEY_ID` to make key material stable across deploys.

## Alternatives Considered

HS256 shared secrets are simpler, but they make key rotation and service isolation weaker.
