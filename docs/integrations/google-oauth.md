# Google OAuth Integration

Verified on: 2026-05-20

Sources:

- https://developers.google.com/identity/openid-connect/reference
- https://developers.google.com/identity/protocols/oauth2/web-server

Prompteer uses Google OAuth through Auth.js. Empty `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` select the local mock OAuth provider.

The mock provider must expose authorization, token, userinfo, and JWKS endpoints and issue RS256 ID tokens.
