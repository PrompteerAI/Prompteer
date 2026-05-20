# Security Policy

## Reporting A Vulnerability

Do not open a public issue for a vulnerability.

Use GitHub Security Advisories for private reports. If advisories are unavailable, contact the maintainer privately through the repository owner's GitHub profile.

Include:

- Affected component or route.
- Reproduction steps or proof of concept.
- Impact and affected data, if known.
- Whether any credentials, tokens, or private data were exposed.

## Supported Versions

| Version | Supported |
| ------- | --------- |
| `main`  | Yes       |

Prompteer has not cut a stable release yet. Security fixes land on `main` until release branches exist.

## Disclosure Timeline

- Acknowledge reports within 72 hours when possible.
- Triage severity and scope before public discussion.
- Patch critical issues within 30 days when a fix is under project control.
- Credit reporters in release notes when they want credit and disclosure is safe.

## Secret Handling

Local development works without real third-party credentials. Leave external API keys blank in `.env` to use mocks.

Never commit:

- `.env` or `.env.*.local`.
- API keys, OAuth secrets, JWT private keys, webhook secrets, or database URLs with real passwords.
- Production data, logs containing tokens, mock captures derived from real user data, or sanitized-but-reversible samples.

## Security Baseline

- Auth.js session cookies stay HTTP-only.
- FastAPI validates RS256 bearer tokens through the web app JWKS.
- API errors use RFC 9457 Problem Details without leaking secrets.
- Cost-sensitive routes have rate limits and LLM quota checks.
- Production must set `AUTH_JWT_PRIVATE_KEY`, `AUTH_SECRET`, and real secret values through the deployment environment.
