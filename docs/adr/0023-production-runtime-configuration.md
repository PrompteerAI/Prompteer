# 0023 - Production Runtime Configuration Guardrails

## Status

Accepted on 2026-05-22.

## Context

Prompteer deliberately falls back to schema-faithful mocks when local
credentials are blank. That is the right development default, but it is unsafe
for a production process to start with mock integrations, seeded login routes,
development bootstrap, or the public local database password.

## Decision

`ENV=production` now makes the API validate its runtime contract during settings
construction. The process fails fast when the database URL uses the committed
development secret, Google OAuth is not fully configured, no LLM provider key is
present, Stripe or SendGrid secrets are missing, or development-only switches
remain enabled.

The API startup log also emits a structured `api_startup` event with integration
modes and non-secret runtime flags. Secret values are never logged.

## Consequences

Production misconfiguration is caught before the app accepts traffic instead of
silently serving mock-backed flows. Local development remains unchanged because
the guard applies only when `ENV=production`.

Operators must set real provider credentials or intentionally keep the
deployment in development mode. Release checks should verify the production env
contract before promoting images.

## Alternatives considered

Readiness-only checks were rejected because an invalid production container
could still boot and briefly accept traffic before probes removed it. Warning
logs were rejected because they are easy to miss during automated deployments.
