#!/usr/bin/env sh
set -eu

api_uvicorn_workers="${API_UVICORN_WORKERS:-1}"
api_uvicorn_workers_max="${API_UVICORN_WORKERS_MAX:-32}"

case "$api_uvicorn_workers" in
  "" | *[!0-9]*)
    echo "API_UVICORN_WORKERS must be a positive integer; got '${api_uvicorn_workers}'." >&2
    exit 64
    ;;
esac

case "$api_uvicorn_workers_max" in
  "" | *[!0-9]*)
    echo "API_UVICORN_WORKERS_MAX must be a positive integer; got '${api_uvicorn_workers_max}'." >&2
    exit 64
    ;;
esac

if [ "${#api_uvicorn_workers}" -gt 4 ]; then
  echo "API_UVICORN_WORKERS must be a positive integer no greater than 9999; got '${api_uvicorn_workers}'." >&2
  exit 64
fi

if [ "${#api_uvicorn_workers_max}" -gt 4 ]; then
  echo "API_UVICORN_WORKERS_MAX must be a positive integer no greater than 9999; got '${api_uvicorn_workers_max}'." >&2
  exit 64
fi

if [ "$api_uvicorn_workers" -lt 1 ]; then
  echo "API_UVICORN_WORKERS must be at least 1; got '${api_uvicorn_workers}'." >&2
  exit 64
fi

if [ "$api_uvicorn_workers_max" -lt 1 ]; then
  echo "API_UVICORN_WORKERS_MAX must be at least 1; got '${api_uvicorn_workers_max}'." >&2
  exit 64
fi

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
  --worker-tmp-dir /dev/shm \
  --access-logfile - \
  --error-logfile - \
  "$@"
