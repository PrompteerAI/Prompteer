# Migration Runbook

Production database changes follow expand-contract:

1. Expand: add the new schema shape without removing the old one.
2. Backfill: migrate existing data with a script or background job.
3. Cutover: switch application reads and writes to the new shape.
4. Contract: remove the old shape after at least one observed release cycle.

Local development migrations may be simpler, but destructive production migrations need either this pattern or an ADR explaining why a one-step migration is safe.
