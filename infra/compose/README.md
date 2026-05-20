# Compose Support

The root `compose.yaml` starts PostgreSQL and Redis by default for local development:

```sh
docker compose up -d
pnpm dev
```

The containerized application topology is behind the `app` profile so it does not conflict with local dev ports:

```sh
docker compose --profile app up -d
```

That profile runs FastAPI, the Celery worker, Next.js, and nginx.
