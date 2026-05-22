#!/usr/bin/env sh
# Installs contributor Git hook tooling after pnpm install.
set -eu

if [ "${HUSKY:-}" = "0" ]; then
  exit 0
fi

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  printf 'Skipping hook install outside a Git worktree.\n'
  exit 0
fi

if ! command -v uv >/dev/null 2>&1; then
  printf 'Missing required command: uv\n' >&2
  printf 'Install uv, then rerun pnpm install to bootstrap Python pre-commit hooks.\n' >&2
  printf 'See https://docs.astral.sh/uv/getting-started/installation/\n' >&2
  exit 127
fi

pnpm exec husky
uv run --project apps/api pre-commit install-hooks
