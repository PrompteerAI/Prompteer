# 0016 — Runtime Google OAuth Mock Signing Key

## Status

Accepted on 2026-05-21.

## Context

The local Google OIDC mock must issue RS256 `id_token` values and publish a matching JWKS so Auth.js can exercise the same flow it uses with Google. The first implementation used a committed PEM private key to keep multiple Gunicorn/Uvicorn workers on the same key, but even dev-only signing material should not live in the repository.

## Decision

Generate a 2048-bit RSA private key at API process startup and store it in the runtime temp directory with `0600` permissions. A small lock file prevents worker races, and all workers reuse the same temp-file key for the lifetime of the process group. The key id remains stable while the public key material is published through `/oauth2/v3/certs`.

## Consequences

The repository no longer contains mock private key material. Restarting the local runtime may rotate the key, which is acceptable because Auth.js discovers the mock provider during the login flow. Multi-worker local runs keep a consistent issuer/JWKS pair.

## Alternatives considered

Keeping a deterministic committed key was simple but violated the mock-secret hygiene expected for a public repository. Generating a different key in every worker avoided persistence but would make JWKS validation flaky under multi-worker Gunicorn.
