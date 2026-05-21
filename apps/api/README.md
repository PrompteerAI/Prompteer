# Prompteer API

FastAPI backend for Prompteer.

```sh
uv sync --dev
uv run fastapi dev app/main.py
```

In development, API startup runs `alembic upgrade head` and idempotent demo seed data when `AUTO_SEED_ON_STARTUP=true`. Use `uv run python -m app.db.seed` to rerun the seed explicitly.

The API container runs Gunicorn with `uvicorn_worker.UvicornWorker`. Set `API_UVICORN_WORKERS` in `.env` to control the number of Uvicorn worker processes; the local default is `1` and the safety ceiling is `API_UVICORN_WORKERS_MAX`. Gunicorn request lifecycle knobs are exposed as `API_GUNICORN_TIMEOUT`, `API_GUNICORN_GRACEFUL_TIMEOUT`, and `API_GUNICORN_KEEPALIVE`, with defaults matching Gunicorn's built-ins.

Database pooling is configured per API or worker process with `DATABASE_POOL_SIZE`, `DATABASE_MAX_OVERFLOW`, and `DATABASE_POOL_TIMEOUT`. The defaults preserve SQLAlchemy's QueuePool behavior: 5 persistent connections, 10 overflow connections, and a 30 second checkout timeout.
