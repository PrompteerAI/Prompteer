#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

# shellcheck source=scripts/lib/load-env.sh
source scripts/lib/load-env.sh
load_env_file ".env"
apply_local_port_env
WEB_LEGACY_PORT="${WEB_LEGACY_PORT:-3001}"
require_tcp_port "WEB_LEGACY_PORT" "$WEB_LEGACY_PORT"
export WEB_LEGACY_PORT

require_command() {
  local command_name="$1"
  if ! command -v "$command_name" >/dev/null 2>&1; then
    printf 'Missing required command: %s\n' "$command_name" >&2
    exit 127
  fi
}

require_command pnpm
require_command uv

if [[ ! -x apps/web-legacy/node_modules/.bin/next ]]; then
  printf 'Installing JavaScript dependencies with pnpm...\n'
  pnpm install --frozen-lockfile
fi

if [[ ! -d apps/api/.venv ]]; then
  printf 'Syncing Python dependencies with uv...\n'
  uv sync --project apps/api --dev
fi

printf 'Prompteer dev: web=http://localhost:%s legacy=http://localhost:%s api=http://localhost:%s\n' "$WEB_PORT" "$WEB_LEGACY_PORT" "$API_PORT"
printf 'Legacy preview uses the primary web app at %s as the Auth.js gateway.\n' "$APP_URL"

trap 'kill 0' INT TERM EXIT
scripts/api-dev.sh &
scripts/web-dev.sh &
scripts/web-legacy-dev.sh &
wait
