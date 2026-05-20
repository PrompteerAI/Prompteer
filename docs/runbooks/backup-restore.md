# Backup and Restore Runbook

Prompteer uses PostgreSQL custom-format dumps (`pg_dump --format=custom`) so restores can be inspected with `pg_restore --list` and replayed with `pg_restore`. The scripts accept the app's SQLAlchemy URL (`postgresql+psycopg://...`) and normalize it for PostgreSQL CLI tools.

```sh
scripts/backup-db.sh ./backups/prompteer.dump
pg_restore --list ./backups/prompteer.dump
scripts/restore-db.sh ./backups/prompteer.dump
```

## Local Restore Drill

Run the round-trip verifier against throwaway databases whenever backup behavior changes:

```sh
make backup-restore-check
```

The verifier creates isolated source and restore databases, runs Alembic migrations, seeds demo data, dumps the source database, restores into the clean target database, and checks sentinel rows for the seeded users and challenges.

Set these variables when the default local credentials do not apply:

```sh
MAINTENANCE_DATABASE_URL=postgresql://user:pass@localhost:5432/postgres \
SOURCE_DATABASE_URL=postgresql://user:pass@localhost:5432/prompteer_backup_source \
RESTORE_DATABASE_URL=postgresql://user:pass@localhost:5432/prompteer_backup_restore \
make backup-restore-check
```

Use `KEEP_BACKUP_RESTORE_DATABASES=true` to leave the throwaway databases behind for manual inspection.

## Production Cadence

Use daily full backups plus hourly WAL archiving as the baseline production cadence. Retain enough daily snapshots to cover operator mistakes that are discovered late, and test restore procedures on a non-production database at least monthly.

## Verification

- Inspect each archive before restore: `pg_restore --list ./backups/prompteer.dump`.
- Restore into a throwaway database before overwriting any shared environment.
- Confirm row counts and key business records after restore.
- Treat dump files as sensitive data. Store them encrypted and restrict access like production database credentials.
