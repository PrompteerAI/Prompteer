# Migration Runbook

Production database changes follow expand-contract:

1. Expand: add the new schema shape without removing the old one.
2. Backfill: migrate existing data with a script or background job.
3. Cutover: switch application reads and writes to the new shape.
4. Contract: remove the old shape after at least one observed release cycle.

Local development migrations may be simpler, but destructive production migrations need either this pattern or an ADR explaining why a one-step migration is safe.

## Startup probe

`GET /api/v1/health/startup` compares the database's current Alembic revision with the repository's Alembic head. It returns `200` only when they match. A `503` response means the database should not receive traffic until migrations are applied or the revision mismatch is investigated.

## Verification

Run `make migration-check` before merging migration changes. It creates a throwaway PostgreSQL database, runs `alembic upgrade head`, `alembic downgrade base`, and `alembic upgrade head` again, then checks that sentinel tables exist. CI runs the same target in the backend job.
