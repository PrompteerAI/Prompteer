#!/usr/bin/env bash
# Builds the primary Next.js app with the local environment contract loaded.
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

# shellcheck source=scripts/lib/load-env.sh
source scripts/lib/load-env.sh
load_env_file ".env"
export ENV="${ENV:-development}"
apply_local_port_env

cd apps/web
exec next build
