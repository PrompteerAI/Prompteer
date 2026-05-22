#!/usr/bin/env bash
# Runs the API, primary web app, and legacy-preview app in hot-reload mode.
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

child_pids=()

start_child() {
  if command -v setsid >/dev/null 2>&1; then
    setsid "$@" &
  else
    "$@" &
  fi
  child_pids+=("$!")
}

cleanup() {
  trap - INT TERM EXIT
  if ((${#child_pids[@]} > 0)); then
    for child_pid in "${child_pids[@]}"; do
      kill -TERM "-$child_pid" >/dev/null 2>&1 || true
    done
    kill "${child_pids[@]}" >/dev/null 2>&1 || true
    wait "${child_pids[@]}" >/dev/null 2>&1 || true
  fi
}

trap cleanup INT TERM EXIT
start_child scripts/api-dev.sh
start_child scripts/web-dev.sh
start_child scripts/web-legacy-dev.sh
wait "${child_pids[@]}"
