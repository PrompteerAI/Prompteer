#!/usr/bin/env bash
# Confirms readiness reports structured diagnostics when Redis is unavailable.
set -euo pipefail

source scripts/lib/load-env.sh

load_env_file ".env"
apply_local_port_env
require_docker_compose

mkdir -p .verify
origin="$(compose_http_origin)"
output_path=".verify/health-ready-redis-down.json"

restart_redis() {
  docker compose start redis >/dev/null 2>&1 || true
}

docker compose stop redis >/dev/null
trap restart_redis EXIT

status_code="$(
  curl \
    --silent \
    --show-error \
    --output "$output_path" \
    --write-out "%{http_code}" \
    "${origin}/api/v1/health/ready" || true
)"

if [[ "$status_code" != "503" ]]; then
  printf 'Expected readiness to return 503 while Redis is stopped, got %s.\n' "$status_code" >&2
  printf 'Response body saved to %s.\n' "$output_path" >&2
  exit 1
fi

node - "$output_path" <<'NODE'
const fs = require("node:fs");

const path = process.argv[2];
const body = JSON.parse(fs.readFileSync(path, "utf8"));
const redis = body?.checks?.redis;

if (body?.status !== "degraded") {
  throw new Error(`Expected degraded readiness status, got ${JSON.stringify(body?.status)}.`);
}

if (!redis || redis.status !== "fail" || typeof redis.detail !== "string") {
  throw new Error(`Expected Redis diagnostic object, got ${JSON.stringify(redis)}.`);
}

if (!redis.detail.includes("Redis ping failed")) {
  throw new Error(`Expected Redis failure detail, got ${JSON.stringify(redis.detail)}.`);
}
NODE

trap - EXIT
restart_redis
scripts/check-compose-health.sh

printf 'Readiness outage check passed; Redis failure body saved to %s.\n' "$output_path"
