# 0024 - Pre-release Timestamp Type Migration

## Status

Accepted on 2026-05-22.

## Context

The initial schema created several domain timestamp columns as PostgreSQL
`timestamp without time zone`. Prompteer stores domain datetimes in UTC and
returns ISO 8601 values with explicit offsets, so those persisted columns should
use timezone-aware types before the first production deployment.

Changing a column type is treated as destructive unless the migration follows
expand-contract or has an ADR explaining why a one-step change is safe.

## Decision

Keep the one-step Alembic migration that converts the pre-release timestamp
columns to `timestamp with time zone` using `AT TIME ZONE 'UTC'`.

The migration is allowed by `destructive_migration_adr` because there is no live
production database yet, and the conversion is deterministic for the seeded and
local development data that exists today.

## Consequences

The persisted schema matches Prompteer's UTC timestamp contract before release.
Future incompatible type changes after production launch must use
expand-contract unless a new ADR justifies the exception.

## Alternatives considered

Keeping naive database timestamps was rejected because it would keep the schema
out of line with the API contract. Adding parallel timestamp columns and
backfilling them was unnecessary before the first production deployment.
