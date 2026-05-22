#!/usr/bin/env bash
# Starts the primary Next.js app in hot-reload mode on WEB_PORT.
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

# shellcheck source=scripts/lib/load-env.sh
source scripts/lib/load-env.sh
load_env_file ".env"
apply_local_port_env

printf 'Prompteer web: http://localhost:%s\n' "$WEB_PORT"
if [[ -z "${GOOGLE_CLIENT_ID:-}" || -z "${GOOGLE_CLIENT_SECRET:-}" ]]; then
  printf 'Mock Google OAuth is ON\n'
fi

pnpm --filter @prompteer/web run locales

cd apps/web
exec pnpm exec next dev --port "$WEB_PORT"
