#!/usr/bin/env bash
# Starts Docker Compose services and waits for the declared health contract.
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

# shellcheck source=scripts/lib/load-env.sh
source scripts/lib/load-env.sh
load_env_file ".env"
apply_local_port_env
require_docker_compose

docker compose up -d "$@"

mapfile -t compose_services < <(docker compose config --services)
services=()
for arg in "$@"; do
  for compose_service in "${compose_services[@]}"; do
    if [[ "$arg" == "$compose_service" ]]; then
      services+=("$arg")
      break
    fi
  done
done

if ((${#services[@]} > 0)); then
  COMPOSE_HEALTH_SERVICES="${services[*]}" COMPOSE_HEALTH_TIMEOUT="${COMPOSE_WAIT_TIMEOUT:-300}" scripts/check-compose-health.sh
else
  COMPOSE_HEALTH_TIMEOUT="${COMPOSE_WAIT_TIMEOUT:-300}" scripts/check-compose-health.sh
fi
