FROM python:3.12-slim@sha256:9d3abd9fc11d06998ccdbdd93b4dd49b5ad7d67fcbbc11c016eb0eb2c2194891 AS builder

WORKDIR /app/apps/api

COPY --from=ghcr.io/astral-sh/uv:0.11.15@sha256:e590846f4776907b254ac0f44b5b380347af5d90d668138ca7938d1b0c2f98d3 /uv /uvx /bin/
ENV UV_PYTHON_DOWNLOADS=0 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

COPY apps/api/pyproject.toml apps/api/uv.lock apps/api/.python-version apps/api/README.md ./
RUN uv sync --no-dev --frozen --no-install-project

FROM python:3.12-slim@sha256:9d3abd9fc11d06998ccdbdd93b4dd49b5ad7d67fcbbc11c016eb0eb2c2194891 AS runtime

WORKDIR /app/apps/api
ARG APP_VERSION=0.1.0
ARG VCS_REF=unknown
LABEL org.opencontainers.image.source="https://github.com/PrompteerAI/Prompteer" \
    org.opencontainers.image.description="Prompteer FastAPI service" \
    org.opencontainers.image.licenses="MIT" \
    org.opencontainers.image.version="${APP_VERSION}" \
    org.opencontainers.image.revision="${VCS_REF}"

ENV PATH="/app/apps/api/.venv/bin:${PATH}" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN useradd --create-home --uid 10001 prompteer

COPY --from=builder --chown=prompteer:prompteer /app/apps/api/.venv ./.venv
COPY --chown=prompteer:prompteer apps/api/app ./app
COPY --chown=prompteer:prompteer --chmod=0755 apps/api/scripts/start.sh ./scripts/start.sh
COPY --chown=prompteer:prompteer apps/api/alembic.ini ./alembic.ini

USER prompteer
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=3s --start-period=30s --retries=3 CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/v1/health/live', timeout=2)"
CMD ["./scripts/start.sh"]
