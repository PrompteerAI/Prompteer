FROM python:3.12-slim AS runtime

WORKDIR /app/apps/api

RUN pip install --no-cache-dir uv

COPY apps/api/pyproject.toml apps/api/uv.lock apps/api/.python-version ./
RUN uv sync --no-dev --frozen

COPY apps/api/app ./app
COPY apps/api/alembic.ini ./alembic.ini

EXPOSE 8000
CMD ["uv", "run", "fastapi", "run", "app/main.py", "--host", "0.0.0.0", "--port", "8000"]
