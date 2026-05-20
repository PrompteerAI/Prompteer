# 0002 - Mock-First External Integrations

## Status

Accepted on 2026-05-20.

## Context

Prompteer depends on OAuth, LLM, payments, and email providers, but local development must work after `cp .env.example .env` with no real credentials.

## Decision

Each external integration has a protocol/interface, a real implementation, a schema-faithful mock implementation, and a factory that selects the implementation from environment variables. Empty credentials explicitly mean mock mode.

## Consequences

Development and CI can exercise full flows without secret provisioning. Mocks must be maintained against vendor API documentation and documented under `docs/integrations/`.

## Alternatives Considered

Hard-coded stubs would be faster initially but would not catch schema drift or integration mistakes.
