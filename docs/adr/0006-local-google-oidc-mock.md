# 0006 - Local Google OIDC Mock

## Status

Accepted on 2026-05-20.

## Context

Local development must work after `cp .env.example .env` with no external API keys. The web app uses Auth.js with Google OAuth, so a blank credential state cannot simply point at Google's production issuer with fake client credentials.

## Decision

When Google credentials are blank, Auth.js keeps the provider id `google` but points to the FastAPI mock issuer configured by `AUTH_MOCK_GOOGLE_ISSUER`. The API exposes Google-shaped authorization, token, userinfo, discovery, and JWKS endpoints and signs ID tokens with a dev-only RS256 key.

The login page offers the seeded admin, paid, and free users by passing `login_hint` through the standard authorization request.

## Consequences

The local login flow exercises Auth.js's real OIDC callback path, including state, nonce, PKCE, token exchange, userinfo, and JWKS validation, without requiring Google credentials. Production must set real Google credentials and disable dev routes.

## Alternatives considered

A browser-only fake login button would have been easier, but it would bypass Auth.js and leave the OAuth callback path untested. A credentials provider would also diverge from the production authentication model.
