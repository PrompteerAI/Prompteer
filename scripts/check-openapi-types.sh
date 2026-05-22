#!/usr/bin/env bash
# Verifies generated OpenAPI and shared TypeScript API types are up to date.
set -euo pipefail

tmpdir="$(mktemp -d)"
trap 'rm -rf "$tmpdir"' EXIT

(
  cd apps/api
  uv run python scripts/export_openapi.py "$tmpdir/openapi-v1.json"
)

pnpm --filter @prompteer/shared-types exec openapi-typescript \
  "$tmpdir/openapi-v1.json" \
  -o "$tmpdir/api.ts"

pnpm exec prettier --write "$tmpdir/openapi-v1.json" "$tmpdir/api.ts"

diff -u docs/api/openapi-v1.json "$tmpdir/openapi-v1.json"
diff -u packages/shared-types/src/api.ts "$tmpdir/api.ts"
