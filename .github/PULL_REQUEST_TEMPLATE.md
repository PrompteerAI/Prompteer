## Summary

<!-- What changed and why? Keep this reviewer-focused. -->

## Verification

- [ ] `make verify`
- [ ] `make migration-check` if migrations changed
- [ ] `make backup-restore-check` if backup/restore behavior changed

## Checklist

- [ ] I updated tests or documented why the existing coverage is sufficient.
- [ ] I regenerated OpenAPI/shared types if API contracts changed.
- [ ] I added or updated screenshots for UI changes.
- [ ] I added an ADR for load-bearing architecture, auth, billing, data, or integration decisions.
- [ ] I considered migrations, rollback, and production config impact.
