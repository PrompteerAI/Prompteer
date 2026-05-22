# 0027 - Node 24 GitHub Actions Runtime

## Status

Accepted on 2026-05-23.

## Context

The image publishing workflow originally used SHA-pinned Docker actions whose
major versions targeted Node.js 20. GitHub now warns that Node.js 20 JavaScript
actions are deprecated and will be removed from hosted runners in 2026. Forcing
those actions to execute on Node.js 24 still produced a warning because the
action metadata continued to target Node.js 20.

AGENTS.md called out `docker/build-push-action@v6` when the workflow was first
specified. That version is now a source of CI warning noise and future runner
risk, while the current Docker action majors publish `using: node24` metadata.

## Decision

Upgrade the Docker image publishing actions to their current Node.js 24 majors
while preserving immutable SHA pins:

- `docker/setup-buildx-action@v4.1.0`
- `docker/login-action@v4.2.0`
- `docker/build-push-action@v7.2.0`

The workflow keeps the same buildx cache, GHCR login, tag, and push behavior.

## Consequences

The Build Images workflow no longer depends on deprecated Node.js 20 action
runtimes. This intentionally supersedes the older v6 action version mentioned in
AGENTS.md because the external runner platform moved forward.

Future action bumps should continue to pin full commit SHAs and verify the action
metadata runtime before merging.

## Alternatives considered

Keeping the v6/v3 Docker actions and setting
`FORCE_JAVASCRIPT_ACTIONS_TO_NODE24=true` was rejected because GitHub still
emitted a deprecation warning for actions whose metadata targeted Node.js 20.

Leaving the warning in place was rejected because image publishing is part of the
main release path and should stay ahead of hosted runner removals.
