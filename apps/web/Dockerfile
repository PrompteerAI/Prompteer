FROM node:22-alpine@sha256:968df39aedcea65eeb078fb336ed7191baf48f972b4479711397108be0966920 AS deps
WORKDIR /app
RUN corepack enable
ENV HUSKY=0
COPY package.json pnpm-lock.yaml pnpm-workspace.yaml turbo.json ./
COPY apps/web/package.json apps/web/package.json
COPY packages packages
RUN pnpm install --frozen-lockfile

FROM deps AS build
COPY apps/web apps/web
COPY scripts scripts
RUN export ENV=development \
    APP_URL=http://localhost \
    AUTH_URL=http://localhost \
    AUTH_JWT_ISSUER=http://localhost \
    AUTH_MOCK_GOOGLE_ISSUER=http://localhost \
    NEXT_PUBLIC_API_URL=http://localhost/api/v1 \
    API_INTERNAL_URL=http://api:8000/api/v1 && \
    pnpm --filter @prompteer/web locales && \
    pnpm --filter @prompteer/web exec next build

FROM node:22-alpine@sha256:968df39aedcea65eeb078fb336ed7191baf48f972b4479711397108be0966920 AS runtime
WORKDIR /app
ENV NODE_ENV=production \
    ENV=production
COPY --from=build --chown=node:node /app/apps/web/.next/standalone ./
COPY --from=build --chown=node:node /app/apps/web/.next/static ./apps/web/.next/static
COPY --from=build --chown=node:node /app/apps/web/public ./apps/web/public
USER node
EXPOSE 3000
HEALTHCHECK --interval=30s --timeout=3s --start-period=30s --retries=3 CMD node -e "require('node:http').get('http://127.0.0.1:3000/api/health', (response) => process.exit(response.statusCode === 200 ? 0 : 1)).on('error', () => process.exit(1))"
CMD ["node", "apps/web/server.js"]
