#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

require_command() {
  local command_name="$1"
  if ! command -v "$command_name" >/dev/null 2>&1; then
    printf 'Missing required command: %s\n' "$command_name" >&2
    exit 127
  fi
}

require_command pnpm
require_command uv
require_command docker

if [[ ! -f .env ]]; then
  cp .env.example .env
  printf 'Created .env from .env.example\n'
fi

pnpm install
uv sync --project apps/api --dev

docker compose up -d --build --wait --wait-timeout "${COMPOSE_WAIT_TIMEOUT:-300}"

(
  cd apps/api
  uv run alembic upgrade head
  uv run python -m app.db.seed
)

printf '\nPrompteer is ready.\n'
printf 'Containerized app: http://localhost\n'
printf 'Hot-reload dev:    pnpm dev, then http://localhost:3000\n'
