#!/usr/bin/env bash
set -euo pipefail

services="${COMPOSE_HEALTH_SERVICES:-postgres redis api worker web nginx}"
timeout_seconds="${COMPOSE_HEALTH_TIMEOUT:-60}"
interval_seconds="${COMPOSE_HEALTH_INTERVAL:-2}"
if command -v python3 >/dev/null; then
  python_bin="python3"
elif command -v python >/dev/null; then
  python_bin="python"
else
  printf 'Missing required Python interpreter: python3 or python\n' >&2
  exit 127
fi

deadline=$((SECONDS + timeout_seconds))
last_output=""

while true; do
  compose_ps_json="$(docker compose ps --format json)"

  if output="$(PROMPTEER_COMPOSE_PS_PAYLOAD="$compose_ps_json" "$python_bin" - "$services" 2>&1 <<'PY'
import json
import os
import sys

expected_services = sys.argv[1].split()
payload = os.environ["PROMPTEER_COMPOSE_PS_PAYLOAD"].strip()

if not payload:
    print("docker compose ps returned no JSON output.", file=sys.stderr)
    sys.exit(1)

try:
    parsed = json.loads(payload)
except json.JSONDecodeError:
    parsed = [json.loads(line) for line in payload.splitlines() if line.strip()]

containers = parsed if isinstance(parsed, list) else [parsed]
by_service = {str(container.get("Service")): container for container in containers}

failures: list[str] = []
for service in expected_services:
    container = by_service.get(service)
    if container is None:
        failures.append(f"{service}: missing from docker compose ps output")
        continue

    state = str(container.get("State", ""))
    health = str(container.get("Health", ""))
    if state != "running" or health != "healthy":
        failures.append(f"{service}: state={state or '<empty>'} health={health or '<empty>'}")

if failures:
    print("Compose health check failed:", file=sys.stderr)
    for failure in failures:
        print(f"  - {failure}", file=sys.stderr)
    sys.exit(1)

print(f"Compose services healthy: {', '.join(expected_services)}")
PY
  )"; then
    printf '%s\n' "$output"
    exit 0
  fi

  last_output="$output"
  if ((SECONDS >= deadline)); then
    printf '%s\n' "$last_output" >&2
    exit 1
  fi

  sleep "$interval_seconds"
done
