# Prompteer Web

Next.js frontend for Prompteer.

```sh
cp ../../.env.example ../../.env
pnpm --filter @prompteer/web dev
```

The package scripts export the repository root `.env` before invoking Next.js, so Auth.js sees the same local configuration as the API.
