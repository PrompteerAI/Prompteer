#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

# shellcheck source=scripts/lib/load-env.sh
source scripts/lib/load-env.sh
load_env_file ".env"
apply_local_port_env

cd apps/api
exec uv run fastapi dev app/main.py --port "$API_PORT"
