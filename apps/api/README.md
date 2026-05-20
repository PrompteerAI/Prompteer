# Prompteer API

FastAPI backend for Prompteer.

```sh
uv sync --dev
uv run fastapi dev app/main.py
```

In development, API startup runs `alembic upgrade head` and idempotent demo seed data when `AUTO_SEED_ON_STARTUP=true`. Use `uv run python -m app.db.seed` to rerun the seed explicitly.
