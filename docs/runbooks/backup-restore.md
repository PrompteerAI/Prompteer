# Backup and Restore Runbook

Use custom-format dumps for PostgreSQL backups:

```sh
scripts/backup-db.sh ./backups/prompteer.dump
pg_restore --list ./backups/prompteer.dump
scripts/restore-db.sh ./backups/prompteer.dump
```

Recommended production cadence is daily full backups plus hourly WAL archiving. Verify restores regularly against a throwaway database.
