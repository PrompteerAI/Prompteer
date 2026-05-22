# 0028 - GHCR Package Linking Metadata

## Status

Accepted on 2026-05-23.

## Context

Prompteer publishes production web and API images to GHCR. GitHub's
[package linking documentation](https://docs.github.com/en/packages/learn-github-packages/connecting-a-repository-to-a-package)
says container images published under a user or organization are not linked to a
source repository by default, and recommends the `org.opencontainers.image.source`
OCI label to connect a container package to the repository. Connected packages
can show repository metadata and may inherit the repository's access permissions
when organization settings allow it.

## Decision

Add OCI image labels to both production Dockerfiles:

- `org.opencontainers.image.source`
- `org.opencontainers.image.description`
- `org.opencontainers.image.licenses`
- `org.opencontainers.image.version`
- `org.opencontainers.image.revision`

The image publishing workflow passes the Git SHA into the label build
arguments, so GHCR images can be traced back to the source revision that built
them.

## Consequences

Future GHCR pushes carry repository-linking metadata and revision provenance.
Package visibility can still be constrained by GitHub organization settings, so
an owner may need to make the first package public in the GitHub UI if automatic
permission inheritance is disabled.

## Alternatives considered

Leaving images unlabeled was rejected because it weakens the README's GHCR
availability claim and makes package-to-source provenance less obvious. Setting
package visibility from the workflow was not chosen because GitHub exposes
visibility controls through package settings and owner policy, while OCI labels
are a code-level contract that travels with every image.
