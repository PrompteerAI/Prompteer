# Prompteer API

FastAPI backend for Prompteer.

```sh
uv sync --dev
uv run fastapi dev app/main.py
```

In development, API startup runs `alembic upgrade head` and idempotent demo seed data when `AUTO_SEED_ON_STARTUP=true`. Use `uv run python -m app.db.seed` to rerun the seed explicitly.

The API container runs Gunicorn with `uvicorn_worker.UvicornWorker`. Set `API_UVICORN_WORKERS` in `.env` to control the number of Uvicorn worker processes; the local default is `1` and the safety ceiling is `API_UVICORN_WORKERS_MAX`.
