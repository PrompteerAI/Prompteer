# Google OAuth Integration

Verified on: 2026-05-22

Sources:

- https://developers.google.com/identity/openid-connect/reference
- https://developers.google.com/identity/protocols/oauth2/web-server

Prompteer uses Google OAuth through Auth.js. Empty `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` select the local mock OpenID Connect provider at `AUTH_MOCK_GOOGLE_ISSUER`.

Hot-reload dev derives the mock issuer and endpoints from `API_PORT`, usually `http://localhost:8000`. Compose uses nginx as the public issuer at `http://localhost` and sets `AUTH_MOCK_GOOGLE_SERVER_BASE_URL=http://api:8000` so discovery can publish internal token, userinfo, and JWKS endpoints for Auth.js server-to-server calls.

## Local mock

The mock provider exposes Google's development-facing endpoint shape:

- `GET /.well-known/openid-configuration`
- `GET /o/oauth2/v2/auth`
- `POST /token`
- `GET /v3/userinfo`
- `GET /oauth2/v3/certs`

The token endpoint returns Google's standard fields for an authorization-code exchange:

```json
{
  "access_token": "ya29...",
  "expires_in": 3600,
  "refresh_token": "1//...",
  "scope": "openid email profile",
  "token_type": "Bearer",
  "id_token": "<RS256 JWT>"
}
```

The `id_token` is signed with a dev-only RS256 key generated at API startup and stored outside the repository in the runtime temp directory. Multiple Gunicorn/Uvicorn workers reuse that runtime key, so token signing and JWKS stay consistent for the lifetime of the local API process group. The public key is published through JWKS and the issuer is the exact `AUTH_MOCK_GOOGLE_ISSUER` value with trailing slashes removed. If `AUTH_MOCK_GOOGLE_SERVER_BASE_URL` is set, only the discovery document's token, userinfo, and JWKS URLs use that internal base; the issuer and authorization endpoint stay public.

`/v3/userinfo` returns schema-compatible profile claims:

```json
{
  "sub": "mock-google-oauth2|free",
  "email": "free@prompteer.dev",
  "email_verified": true,
  "name": "Free Prompt Builder",
  "given_name": "Free",
  "family_name": "Builder",
  "picture": "https://prompteer.dev/mock-avatars/free.png",
  "locale": "en"
}
```

The mock supports three seeded login hints: `admin@prompteer.dev`, `paid@prompteer.dev`, and `free@prompteer.dev`. Unknown or absent hints resolve to the free demo account.

The mock is disabled when real Google credentials are present or when dev routes are disabled.
