#!/usr/bin/env bash
# Bootstraps a contributor machine by installing deps, starting Compose, and seeding data.
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

# shellcheck source=scripts/lib/load-env.sh
source scripts/lib/load-env.sh

require_command pnpm
require_command uv
require_docker_compose

if [[ ! -f .env ]]; then
  cp .env.example .env
  printf 'Created .env from .env.example\n'
fi

load_env_file ".env"
apply_local_port_env

pnpm install
uv sync --project apps/api --dev

scripts/compose-up.sh --build

(
  cd apps/api
  uv run python -m app.db.seed
)

printf '\nPrompteer is ready.\n'
printf 'Containerized app: %s\n' "$(compose_http_origin)"
printf 'Hot-reload dev:    pnpm dev, then http://localhost:%s\n' "${WEB_PORT:-3000}"
