#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

# shellcheck source=scripts/lib/load-env.sh
source scripts/lib/load-env.sh
load_env_file ".env"
export ENV="${ENV:-development}"
WEB_LEGACY_PORT="${WEB_LEGACY_PORT:-3001}"
require_tcp_port "WEB_LEGACY_PORT" "$WEB_LEGACY_PORT"
export WEB_LEGACY_PORT

cd apps/web-legacy
exec next build
