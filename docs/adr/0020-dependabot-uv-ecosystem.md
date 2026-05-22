# 0020 - Dependabot Uses The uv Ecosystem

## Status

Accepted on 2026-05-22.

## Context

Prompteer manages the backend with `uv`, committing `apps/api/pyproject.toml`
and `apps/api/uv.lock` as the reproducible dependency source of truth. Older
Python Dependabot guidance often used `package-ecosystem: "pip"` for
`pyproject.toml` projects, but that does not express the lockfile owner for this
repo. Current GitHub Dependabot documentation lists `uv` as a supported
ecosystem, and the uv documentation shows `package-ecosystem: "uv"` for
updating `uv.lock`.

Sources verified on 2026-05-22:

- https://docs.github.com/en/code-security/reference/supply-chain-security/supported-ecosystems-and-repositories
- https://docs.astral.sh/uv/guides/integration/dependabot/

## Decision

Keep `.github/dependabot.yaml` on `package-ecosystem: uv` for `/apps/api`.
This lets Dependabot update the backend through the same package manager and
lockfile the project uses locally, in CI, and in Docker images.

## Consequences

Backend dependency PRs are expected to modify `uv.lock` directly. If GitHub
changes uv support semantics, the Dependabot config should be revisited rather
than falling back to pip by default.

## Alternatives considered

Using `package-ecosystem: pip` would satisfy older generic Python guidance, but
it would make the bot less explicit about `uv.lock` ownership and would diverge
from the backend's actual package-management workflow.
