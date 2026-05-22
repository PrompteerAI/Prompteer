#!/usr/bin/env bash
# Starts the legacy-preview Next.js app in hot-reload mode on WEB_LEGACY_PORT.
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

# shellcheck source=scripts/lib/load-env.sh
source scripts/lib/load-env.sh
load_env_file ".env"
WEB_LEGACY_PORT="${WEB_LEGACY_PORT:-3001}"
require_tcp_port "WEB_LEGACY_PORT" "$WEB_LEGACY_PORT"
export WEB_LEGACY_PORT

printf 'Prompteer legacy web: http://localhost:%s\n' "$WEB_LEGACY_PORT"

cd apps/web-legacy
exec pnpm exec next dev --port "$WEB_LEGACY_PORT"
