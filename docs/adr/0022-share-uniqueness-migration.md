# 0022 - Share Uniqueness Migration

## Status

Accepted on 2026-05-22.

## Context

Prompt runs can be published to the review board as `shares`. The product only
shows one current public run per user and challenge, but early local rebuild
data allowed duplicate rows. Migration `a4d9c2f81b6a` removes duplicate share
rows and adds a unique `(user_id, challenge_id)` index.

This is a destructive data cleanup. The repository is still pre-release and no
production database exists, so there is no deployed write path or external user
data to preserve across an expand-contract cycle.

## Decision

Keep the one-step cleanup migration for the pre-release schema. The migration
keeps the most recently updated share in each duplicate group, deletes older
duplicates, and then creates the unique index that matches the service contract.

Future destructive migrations after any production deployment must follow the
expand-contract runbook unless a separate ADR explains why a one-step contract
is safe.

## Consequences

Local and CI databases get deterministic review-board behavior immediately, and
the service layer can safely upsert a user's share for a challenge without
ambiguous reads. If a production deployment exists later, duplicate cleanup must
be backfilled and audited before adding or validating the constraint.

## Alternatives considered

An expand-contract sequence with a new canonical-share table would be safer for
live production data, but it adds unnecessary migration surface before the first
release. Leaving duplicates possible was rejected because board reads and
prompt-run publishing would stay ambiguous.
