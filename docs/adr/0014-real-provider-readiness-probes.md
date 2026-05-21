# 0014 - Real Provider Readiness Probes

## Status

Accepted on 2026-05-21.

## Context

The API readiness endpoint already checked PostgreSQL, Redis, and whether an
integration was configured for real or mock mode. In real mode, however, it only
proved that credentials existed. That left `/api/v1/health/ready` unable to
detect an unreachable or unauthorized provider until a user hit the affected
workflow.

AGENTS.md requires readiness to pass only when DB, Redis, and required
integrations are reachable.

## Decision

Real-mode readiness now performs low-cost upstream probes with short timeouts:

- Google OAuth: fetch OIDC discovery and then the discovered JWKS URI.
- OpenAI: retrieve the configured chat model.
- Anthropic: call the Messages token-count endpoint for the configured model.
- Stripe: retrieve account balance.
- SendGrid: retrieve API key scopes and require `mail.send`.

The probes use the shared outbound HTTP wrapper so request logging, timeouts,
and redaction match normal integration clients. Provider checks run concurrently
inside readiness to avoid serial latency when several real integrations are
enabled.

Sources verified on 2026-05-21:

- https://developers.openai.com/api/reference/resources/models/methods/retrieve
- https://platform.claude.com/docs/en/api/messages/count_tokens
- https://docs.stripe.com/api/balance
- https://www.twilio.com/docs/sendgrid/api-reference/api-key-permissions/retrieve-a-list-of-scopes-for-which-this-user-has-access
- https://developers.google.com/identity/openid-connect/openid-connect

## Consequences

Readiness can fail before serving traffic when real provider credentials are
invalid, scoped incorrectly, or the provider endpoint is unreachable. Local mock
mode remains offline and still passes when dev routes are enabled.

The endpoint may perform outbound network calls in real mode, so each provider
probe uses a two-second timeout and no retries. Operators should keep readiness
probe intervals conservative enough for external dependency checks.

## Alternatives Considered

Credential-presence checks were faster but did not satisfy the reachability
contract. Full end-to-end API calls, such as creating checkout sessions or
sending emails, were rejected because readiness must not create billable or
user-visible side effects.
