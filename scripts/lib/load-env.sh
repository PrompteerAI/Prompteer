#!/usr/bin/env bash
# Shared local .env loading and port derivation helpers for shell entrypoints.

require_command() {
  local command_name="$1"
  if ! command -v "$command_name" >/dev/null 2>&1; then
    printf 'Missing required command: %s\n' "$command_name" >&2
    exit 127
  fi
}

require_docker_compose() {
  if ! command -v docker >/dev/null 2>&1; then
    printf 'Docker Engine with Docker Compose v2 is required.\n' >&2
    printf 'Install Docker Desktop with WSL integration enabled, or install Docker Engine, before running this command.\n' >&2
    exit 127
  fi

  if ! docker compose version >/dev/null 2>&1; then
    printf 'Docker Compose v2 is required, but `docker compose` is not available.\n' >&2
    printf 'Install or update Docker Desktop / Docker Engine with the Compose v2 plugin before running this command.\n' >&2
    exit 127
  fi

  if ! docker info >/dev/null 2>&1; then
    printf 'Docker Engine is installed but not reachable.\n' >&2
    printf 'Start Docker Desktop, enable WSL integration if applicable, then rerun this command.\n' >&2
    exit 1
  fi
}

load_env_file() {
  local env_file="${1:-.env}"
  [[ -f "$env_file" ]] || return 0

  local line key value
  while IFS= read -r line || [[ -n "$line" ]]; do
    line="${line%$'\r'}"
    [[ -z "${line//[[:space:]]/}" || "$line" =~ ^[[:space:]]*# ]] && continue
    [[ "$line" == *=* ]] || continue

    key="${line%%=*}"
    value="${line#*=}"
    key="${key#"${key%%[![:space:]]*}"}"
    key="${key%"${key##*[![:space:]]}"}"
    [[ "$key" =~ ^[A-Za-z_][A-Za-z0-9_]*$ ]] || continue
    [[ -v "$key" ]] && continue

    if [[ "$value" == \"*\" && "$value" == *\" && ${#value} -ge 2 ]]; then
      value="${value:1:${#value}-2}"
    fi

    export "$key=$value"
  done <"$env_file"
}

require_tcp_port() {
  local name="$1"
  local value="$2"

  if [[ ! "$value" =~ ^[0-9]+$ ]]; then
    printf '%s must be a TCP port number, got: %s\n' "$name" "$value" >&2
    exit 2
  fi

  if [[ ${#value} -gt 5 ]] || ((10#$value < 1 || 10#$value > 65535)); then
    printf '%s must be between 1 and 65535, got: %s\n' "$name" "$value" >&2
    exit 2
  fi
}

apply_local_port_env() {
  local web_port="${WEB_PORT:-3000}"
  local api_port="${API_PORT:-8000}"
  local http_port="${HTTP_PORT:-80}"
  local postgres_port="${POSTGRES_PORT:-55432}"
  local redis_port="${REDIS_PORT:-56379}"
  local postgres_user="${POSTGRES_USER:-prompteer}"
  local postgres_password="${POSTGRES_PASSWORD:-prompteer}"
  local postgres_db="${POSTGRES_DB:-prompteer}"
  local default_database_url="postgresql+psycopg://prompteer:prompteer@localhost:55432/prompteer"
  local default_redis_url="redis://localhost:56379/0"

  require_tcp_port "WEB_PORT" "$web_port"
  require_tcp_port "API_PORT" "$api_port"
  require_tcp_port "HTTP_PORT" "$http_port"
  require_tcp_port "POSTGRES_PORT" "$postgres_port"
  require_tcp_port "REDIS_PORT" "$redis_port"

  export WEB_PORT="$web_port"
  export API_PORT="$api_port"
  export HTTP_PORT="$http_port"
  export POSTGRES_PORT="$postgres_port"
  export REDIS_PORT="$redis_port"

  export APP_URL="http://localhost:${web_port}"
  export AUTH_URL="$APP_URL"
  export AUTH_JWT_ISSUER="$APP_URL"
  export AUTH_JWKS_URL="${APP_URL}/api/auth/jwks"
  export NEXT_PUBLIC_API_URL="http://localhost:${api_port}/api/v1"
  export API_INTERNAL_URL="$NEXT_PUBLIC_API_URL"
  export AUTH_MOCK_GOOGLE_ISSUER="http://localhost:${api_port}"

  if [[ "${DATABASE_URL:-$default_database_url}" == "$default_database_url" ]]; then
    export DATABASE_URL="postgresql+psycopg://${postgres_user}:${postgres_password}@localhost:${postgres_port}/${postgres_db}"
  fi
  if [[ "${REDIS_URL:-$default_redis_url}" == "$default_redis_url" ]]; then
    export REDIS_URL="redis://localhost:${redis_port}/0"
  fi
  if [[ "${RATE_LIMIT_STORAGE_URL:-$default_redis_url}" == "$default_redis_url" ]]; then
    export RATE_LIMIT_STORAGE_URL="$REDIS_URL"
  fi
}

compose_http_origin() {
  local http_port="${HTTP_PORT:-80}"
  require_tcp_port "HTTP_PORT" "$http_port"

  if [[ "$http_port" == "80" ]]; then
    printf 'http://localhost\n'
    return
  fi

  printf 'http://localhost:%s\n' "$http_port"
}

apply_compose_verification_env() {
  local origin
  origin="$(compose_http_origin)"

  if [[ -z "${PLAYWRIGHT_BASE_URL:-}" || "${PLAYWRIGHT_BASE_URL:-}" == "http://localhost" ]]; then
    export PLAYWRIGHT_BASE_URL="$origin"
  fi
  if [[ -z "${PROMPTEER_WEB_URL:-}" || "${PROMPTEER_WEB_URL:-}" == "http://localhost/en" ]]; then
    export PROMPTEER_WEB_URL="${origin}/en"
  fi
}
