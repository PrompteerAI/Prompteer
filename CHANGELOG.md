# Changelog

All notable changes to Prompteer will be documented in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project uses Conventional Commits.

## [Unreleased]

### Added

- Clean monorepo rewrite of the earlier Prompteer prototype.
- Next.js App Router web app with Auth.js, next-intl routing, and seeded demo login.
- FastAPI backend with SQLModel, Alembic, structured logging, Problem Details, and health probes.
- Mock-first integrations for Google OAuth, OpenAI, Anthropic, Stripe, and SendGrid.
- Development seed data, mock mailbox captures, and `/dev/mailbox` viewer.
- LLM rate limits and per-user daily token quota tracking.
- OpenAPI snapshot generation and shared TypeScript API types.
- GitHub Actions, Docker Compose, nginx, backup/restore scripts, and runbooks.

### Changed

- Replaced the legacy split Vite + React and FastAPI repositories with one production-ready monorepo.

### Deprecated

- Nothing yet.

### Removed

- Nothing yet.

### Fixed

- Nothing yet.

### Security

- Added RS256 Auth.js JWT validation in the API and kept browser tokens out of client JavaScript through a same-origin API proxy.
