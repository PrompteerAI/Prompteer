# Compose Support

The root `compose.yaml` starts the full stack by default behind nginx:

```sh
docker compose up -d
```

Open `http://localhost` for the containerized app. If `HTTP_PORT` is changed in
`.env`, open `http://localhost:<HTTP_PORT>`; Compose also injects that port into
Auth.js, API JWT issuer checks, and the mock OAuth public issuer.

For native hot-reload development, keep Compose running and start the dev servers:

```sh
pnpm dev
```

The web and API containers do not publish host ports 3000 or 8000, so `pnpm dev` can bind those ports. To start only PostgreSQL and Redis, run:

```sh
docker compose up -d postgres redis
```
