#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

# shellcheck source=scripts/lib/load-env.sh
source scripts/lib/load-env.sh
load_env_file ".env"
apply_local_port_env

printf 'Prompteer dev: web=http://localhost:%s api=http://localhost:%s\n' "$WEB_PORT" "$API_PORT"
if [[ -z "${GOOGLE_CLIENT_ID:-}" || -z "${GOOGLE_CLIENT_SECRET:-}" ]]; then
  printf 'Mock Google OAuth is ON\n'
fi

trap 'kill 0' INT TERM EXIT
scripts/api-dev.sh &
scripts/web-dev.sh &
wait
