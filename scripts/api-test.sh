#!/usr/bin/env bash
# Runs the API pytest suite with local environment defaults loaded.
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

# shellcheck source=scripts/lib/load-env.sh
source scripts/lib/load-env.sh
load_env_file ".env"
apply_local_port_env

cd apps/api
exec uv run pytest "$@"
