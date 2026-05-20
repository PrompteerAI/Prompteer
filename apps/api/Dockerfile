FROM python:3.12-slim AS runtime

WORKDIR /app

RUN pip install --no-cache-dir uv

COPY pyproject.toml uv.lock* ./
RUN uv sync --no-dev || uv sync

COPY app ./app
COPY alembic.ini ./alembic.ini

EXPOSE 8000
CMD ["uv", "run", "fastapi", "run", "app/main.py", "--port", "8000"]
