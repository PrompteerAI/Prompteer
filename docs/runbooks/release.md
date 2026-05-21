# Release Runbook

Prompteer releases are cut from `main` after CI is green and the container images
for the target commit have been pushed to GHCR.

## Preconditions

- Confirm the release commit is on `main` and has passing `ci.yaml`,
  `build.yaml`, and `e2e.yaml` workflow runs.
- Review dependency updates and security advisories before tagging:

  ```sh
  pnpm audit --audit-level moderate
  tmpfile="$(mktemp)"
  trap 'rm -f "$tmpfile"' EXIT
  uv export --project apps/api --frozen --no-dev --format requirements-txt --no-hashes > "$tmpfile"
  uvx pip-audit --progress-spinner off --requirement "$tmpfile"
  ```

- If `pip-audit` reports an advisory with no compatible fix, record the advisory
  ID in the release notes with the mitigation or deferral reason.
- Confirm the generated OpenAPI snapshot and TypeScript types are current:

  ```sh
  make types-check
  ```

## Cut The Release

1. Update `CHANGELOG.md` with the release date and user-facing changes.
2. Create an annotated tag:

   ```sh
   git tag -a vX.Y.Z -m "vX.Y.Z"
   git push origin vX.Y.Z
   ```

3. Wait for image publishing to complete and verify both images exist:

   ```text
   ghcr.io/<owner>/prompteer-web:vX.Y.Z
   ghcr.io/<owner>/prompteer-api:vX.Y.Z
   ```

4. Create the GitHub release from the changelog entry and link the successful CI
   and build workflow runs.

## Post-Release Checks

- Start the tagged images in a disposable environment with blank external
  provider keys and confirm the mock-first path still works.
- Run the health probes through the public origin:

  ```sh
  curl --fail https://<host>/api/v1/health/live
  curl --fail https://<host>/api/v1/health/ready
  curl --fail https://<host>/api/v1/health/startup
  ```

- Verify login, prompt execution, mock checkout completion, and mock mailbox
  access with the seeded accounts.
