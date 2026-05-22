FROM node:26-alpine@sha256:7c6af15abe4e3de859690e7db171d0d711bf37d27528eddfe625b2fe89e097f8 AS deps
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
ARG APP_VERSION=0.1.0
ARG PUBLIC_ORIGIN=https://prompteer.example.invalid
ARG NEXT_PUBLIC_API_URL=https://prompteer.example.invalid/api/v1
ARG NEXT_PUBLIC_APP_VERSION=0.1.0
ARG NEXT_PUBLIC_USE_MOCK_GOOGLE=false
ARG NEXT_PUBLIC_SENTRY_DSN=
RUN export NODE_ENV=production \
    ENV=production \
    APP_VERSION="${APP_VERSION}" \
    NEXT_PUBLIC_APP_VERSION="${NEXT_PUBLIC_APP_VERSION}" \
    APP_URL="${PUBLIC_ORIGIN}" \
    AUTH_URL="${PUBLIC_ORIGIN}" \
    AUTH_JWT_ISSUER="${PUBLIC_ORIGIN}" \
    AUTH_MOCK_GOOGLE_ISSUER="${PUBLIC_ORIGIN}" \
    AUTH_SECRET=build-time-auth-placeholder \
    AUTH_JWT_PRIVATE_KEY=build-time-jwt-placeholder \
    AUTH_JWT_KEY_ID=prompteer-build-auth \
    GOOGLE_CLIENT_ID=build-google-client-id \
    GOOGLE_CLIENT_SECRET=build-google-provider-placeholder \
    NEXT_PUBLIC_API_URL="${NEXT_PUBLIC_API_URL}" \
    NEXT_PUBLIC_USE_MOCK_GOOGLE="${NEXT_PUBLIC_USE_MOCK_GOOGLE}" \
    NEXT_PUBLIC_SENTRY_DSN="${NEXT_PUBLIC_SENTRY_DSN}" \
    API_INTERNAL_URL=http://api:8000/api/v1 && \
    pnpm --filter @prompteer/web locales && \
    pnpm --filter @prompteer/web exec next build

FROM node:26-alpine@sha256:7c6af15abe4e3de859690e7db171d0d711bf37d27528eddfe625b2fe89e097f8 AS runtime
WORKDIR /app
ARG APP_VERSION=0.1.0
LABEL org.opencontainers.image.source="https://github.com/PrompteerAI/Prompteer" \
    org.opencontainers.image.description="Prompteer Next.js web app" \
    org.opencontainers.image.licenses="MIT" \
    org.opencontainers.image.version="${APP_VERSION}" \
    org.opencontainers.image.revision="${APP_VERSION}"
ENV NODE_ENV=production \
    ENV=production
COPY --from=build --chown=node:node /app/apps/web/.next/standalone ./
COPY --from=build --chown=node:node /app/apps/web/.next/static ./apps/web/.next/static
COPY --from=build --chown=node:node /app/apps/web/public ./apps/web/public
USER node
EXPOSE 3000
HEALTHCHECK --interval=30s --timeout=3s --start-period=30s --retries=3 CMD node -e "require('node:http').get('http://127.0.0.1:3000/api/health', (response) => process.exit(response.statusCode === 200 ? 0 : 1)).on('error', () => process.exit(1))"
CMD ["node", "apps/web/server.js"]
