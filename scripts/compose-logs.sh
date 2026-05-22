#!/usr/bin/env bash
# Streams local Docker Compose logs after confirming Docker is available.
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

# shellcheck source=scripts/lib/load-env.sh
source scripts/lib/load-env.sh
load_env_file ".env"
apply_local_port_env
require_docker_compose

docker compose logs "$@"
