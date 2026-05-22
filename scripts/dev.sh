#!/usr/bin/env bash
# Runs the API and primary web app in hot-reload development mode.
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
    case "$command_name" in
      pnpm)
        printf 'Install Node 22, then run: corepack enable\n' >&2
        ;;
      uv)
        printf 'Install uv: https://docs.astral.sh/uv/getting-started/installation/\n' >&2
        ;;
    esac
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
wait "${child_pids[@]}"
