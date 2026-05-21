# Prompteer Web

Next.js frontend for Prompteer.

```sh
cp ../../.env.example ../../.env
pnpm --filter @prompteer/web dev
```

The package scripts export the repository root `.env` before invoking Next.js, so Auth.js sees the same local configuration as the API.

## Locales

English is the only shipped locale at launch. To add another locale, add a
complete JSON file under `src/messages/<locale>.json`; the web package scripts
generate the next-intl locale manifest from those files before dev, build, lint,
typecheck, test, and e2e runs.
