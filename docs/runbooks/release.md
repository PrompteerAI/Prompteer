# Release Runbook

Prompteer releases are cut from `main` after CI is green and the container images
for the target commit have been pushed to GHCR.

## Preconditions

- Confirm the release commit is on `main` and has passing `ci.yaml`,
  `build.yaml`, and `e2e.yaml` workflow runs.
- `build.yaml` publishes GHCR images only after its `required verification` job
  passes. That job repeats the lightweight release gate (`format:check`,
  environment documentation checks, dependency audit, lint, typecheck, unit
  tests, generated API type checks, and frontend builds) before the workflow
  logs in to GHCR.
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

## Repository Hooks

`package.json` intentionally keeps `prepare` as `husky || true`. Docker image
builds run `pnpm install` from a context where `.git` is ignored, so Husky cannot
install hooks there; the tolerant prepare script prevents that expected
container-only state from blocking image builds. Local hook bodies are wired
through package scripts, currently `pnpm run hooks:pre-commit`, so contributors
can run the same checks manually without invoking Git.

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
