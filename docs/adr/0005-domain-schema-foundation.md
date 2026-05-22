# 0005 - Domain Schema Foundation

## Status

Accepted on 2026-05-20.

## Context

The legacy backend modeled users, profiles, challenges, shares, posts, comments, media references, and likes with SQLModel. It also stored plaintext passwords and created tables at application startup.

The rebuild uses Auth.js for identity and Alembic for schema changes.

## Decision

The initial domain schema keeps the legacy product concepts while changing the persistence foundation:

- Users use UUID string identifiers and `auth_subject` instead of local passwords.
- Challenge, share, and post tables preserve `ps`, `img`, and `video` categories.
- Type-specific detail tables model programming testcases, image/video references, and generated shares.
- Like tables use composite primary keys.
- Alembic owns schema creation.

## Consequences

Future API routes can build on stable table names and foreign keys. Seed data can now create realistic demo users, challenges, shares, and board content without reviving local password auth.

## Alternatives considered

Copying the legacy schema directly would have been faster, but it would preserve password storage and startup table creation patterns that the rebuild explicitly replaces.
