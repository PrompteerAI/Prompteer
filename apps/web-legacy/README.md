# Prompteer Legacy Preview

`apps/web-legacy` is a separate Next.js frontend that recreates the visual language of the original `Prompteer__Front` Vite app while using the rebuilt backend APIs.

Run it with:

```sh
cp .env.example .env
./scripts/compose-up.sh postgres redis
pnpm dev:legacy
```

The preview listens on `WEB_LEGACY_PORT` (`3001` by default). The primary `apps/web` frontend still owns Auth.js, JWKS, and the same-origin API gateway on `WEB_PORT` (`3000` by default). `web-legacy` proxies authenticated calls through that gateway instead of minting its own API tokens.
