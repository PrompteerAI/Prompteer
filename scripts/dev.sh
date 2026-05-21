#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

# shellcheck source=scripts/lib/load-env.sh
source scripts/lib/load-env.sh
load_env_file ".env"
apply_local_port_env

require_command() {
  local command_name="$1"
  if ! command -v "$command_name" >/dev/null 2>&1; then
    printf 'Missing required command: %s\n' "$command_name" >&2
    exit 127
  fi
}

require_command pnpm
require_command uv

if [[ ! -x apps/web/node_modules/.bin/next ]]; then
  printf 'Installing JavaScript dependencies with pnpm...\n'
  pnpm install --frozen-lockfile
fi

if [[ ! -d apps/api/.venv ]]; then
  printf 'Syncing Python dependencies with uv...\n'
  uv sync --project apps/api --dev
fi

printf 'Prompteer dev: web=http://localhost:%s api=http://localhost:%s\n' "$WEB_PORT" "$API_PORT"
if [[ -z "${GOOGLE_CLIENT_ID:-}" || -z "${GOOGLE_CLIENT_SECRET:-}" ]]; then
  printf 'Mock Google OAuth is ON\n'
fi

trap 'kill 0' INT TERM EXIT
scripts/api-dev.sh &
scripts/web-dev.sh &
wait
