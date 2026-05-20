## Summary

<!-- What changed and why? Keep this reviewer-focused. -->

## Verification

- [ ] `pnpm lint`
- [ ] `pnpm typecheck`
- [ ] `pnpm test`
- [ ] `pnpm build`
- [ ] `cd apps/api && uv run pytest`
- [ ] `make types-check`

## Checklist

- [ ] I updated tests or documented why the existing coverage is sufficient.
- [ ] I regenerated OpenAPI/shared types if API contracts changed.
- [ ] I added or updated screenshots for UI changes.
- [ ] I added an ADR for load-bearing architecture, auth, billing, data, or integration decisions.
- [ ] I considered migrations, rollback, and production config impact.
