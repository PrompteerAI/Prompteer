#!/usr/bin/env sh
set -eu

api_uvicorn_workers="${API_UVICORN_WORKERS:-1}"
api_uvicorn_workers_max="${API_UVICORN_WORKERS_MAX:-32}"
api_gunicorn_timeout="${API_GUNICORN_TIMEOUT:-30}"
api_gunicorn_graceful_timeout="${API_GUNICORN_GRACEFUL_TIMEOUT:-30}"
api_gunicorn_keepalive="${API_GUNICORN_KEEPALIVE:-2}"

validate_integer() {
  variable_name="$1"
  variable_value="$2"
  minimum_value="$3"
  max_digits="$4"

  case "$variable_value" in
    "" | *[!0-9]*)
      echo "${variable_name} must be an integer >= ${minimum_value}; got '${variable_value}'." >&2
      exit 64
      ;;
  esac

  if [ "${#variable_value}" -gt "$max_digits" ]; then
    echo "${variable_name} must be an integer with at most ${max_digits} digits; got '${variable_value}'." >&2
    exit 64
  fi

  if [ "$variable_value" -lt "$minimum_value" ]; then
    echo "${variable_name} must be at least ${minimum_value}; got '${variable_value}'." >&2
    exit 64
  fi
}

validate_integer API_UVICORN_WORKERS "$api_uvicorn_workers" 1 4
validate_integer API_UVICORN_WORKERS_MAX "$api_uvicorn_workers_max" 1 4
validate_integer API_GUNICORN_TIMEOUT "$api_gunicorn_timeout" 0 6
validate_integer API_GUNICORN_GRACEFUL_TIMEOUT "$api_gunicorn_graceful_timeout" 0 6
validate_integer API_GUNICORN_KEEPALIVE "$api_gunicorn_keepalive" 0 6

if [ "$api_uvicorn_workers" -gt "$api_uvicorn_workers_max" ]; then
  echo "API_UVICORN_WORKERS must be <= API_UVICORN_WORKERS_MAX (${api_uvicorn_workers_max}); got '${api_uvicorn_workers}'." >&2
  exit 64
fi

case "${AUTO_SEED_ON_STARTUP:-true}" in
  1 | true | TRUE | yes | YES | on | ON)
    if [ "${ENV:-development}" != "production" ]; then
      python -m app.core.bootstrap
      export AUTO_SEED_ON_STARTUP=false
    fi
    ;;
esac

exec gunicorn app.main:app \
  --bind 0.0.0.0:8000 \
  --workers "$api_uvicorn_workers" \
  --worker-class uvicorn_worker.UvicornWorker \
  --timeout "$api_gunicorn_timeout" \
  --graceful-timeout "$api_gunicorn_graceful_timeout" \
  --keep-alive "$api_gunicorn_keepalive" \
  --worker-tmp-dir /dev/shm \
  --access-logfile - \
  --error-logfile - \
  "$@"
