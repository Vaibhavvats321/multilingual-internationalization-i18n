# Multilingual Event Platform

One application that serves **many** event websites, each published in
several languages, with a shared organizer dashboard.

> **Phase 0 — repository and decisions.** This repository currently contains
> the project skeleton, the quality gates, the health checks, the decision
> records and the CI baseline. The domain features (events, translations,
> registrations) are built in the phases listed in `PROJECT_SPEC.md` §10.

## Status

| Area | State |
| --- | --- |
| Repository layout, tooling, lockfiles | done |
| API skeleton: config, logging, errors, middleware, health endpoints | done |
| Web skeleton: locale routing, message catalogs, health proxy | done |
| Unit and integration tests | done |
| CI quality gates (lint, types, tests, security audit) | done |
| ADRs, architecture and runbooks | done |
| Domain modules (events, translations, registrations) | Phase 1+ |

## Prerequisites

| Tool | Version | Notes |
| --- | --- | --- |
| Python | 3.13.x | `.python-version` |
| uv | 0.12.x | manages `api/uv.lock` |
| Node.js | **22.23.2** | `.nvmrc`; 22 LTS |
| pnpm | 10.26.2 | `packageManager` in `web/package.json` |
| PostgreSQL | 18 | or Docker with `compose.yaml` |

Node 22.23.2 is a hard requirement, not a preference: `jsdom@30.1.3`
requires `^22.22.2 || ^24.15.0 || >=26.0.0`, and its dependency
`undici@8.12.3` uses the zlib zstd API that only exists from Node 22.15.0.
On older 22.x releases every Vitest worker crashes while loading `undici`.

## Setup

```bash
cp .env.example .env
# set SESSION_SECRET to a random value:
python -c "import secrets; print(secrets.token_urlsafe(48))"

# database
docker compose up -d postgres          # or: createdb -U postgres multilingua

# dependencies
cd api && uv sync --frozen --all-groups
cd ../web && pnpm install --frozen-lockfile
```

Full instructions, including the native PostgreSQL path, are in
[`docs/runbooks/local-development.md`](docs/runbooks/local-development.md).

## Running

```bash
# API - http://localhost:8000
cd api && uv run python -m app --reload

# Web - http://localhost:3000
cd web && pnpm dev
```

Start the API with `python -m app`, not with a bare `uvicorn` command: the
module installs the selector event loop that psycopg requires on Windows
([ADR 0002](docs/decisions/0002-database-access-style.md)).

| URL | Purpose |
| --- | --- |
| <http://localhost:8000/api/v1/health/live> | API liveness |
| <http://localhost:8000/api/v1/health/ready> | API readiness (database) |
| <http://localhost:8000/api/v1/openapi.json> | OpenAPI document |
| <http://localhost:3000/en> | Platform shell (also `/ar`, `/de`) |
| <http://localhost:3000/api/health/live> | Web liveness |
| <http://localhost:3000/api/health/ready> | Web readiness (API) |

## Configuration

All settings are documented in [`.env.example`](.env.example). The real
`.env` is git-ignored.

| Variable | Required | Description |
| --- | --- | --- |
| `APP_ENV` | no | `local` \| `ci` \| `staging` \| `production` |
| `API_BASE_URL` | no | Public base URL of the API |
| `WEB_BASE_URL` | no | Public base URL of the web application |
| `DATABASE_URL` | outside local/ci | PostgreSQL connection string |
| `SESSION_SECRET` | outside local/ci | Secret for session/CSRF key material |
| `CORS_ORIGINS` | no | Comma separated list of allowed origins |
| `LOG_LEVEL` | no | `debug` \| `info` \| `warning` \| `error` |
| `TRANSLATION_PROVIDER` | no | `none` (default) disables machine translation |
| `TRANSLATION_API_KEY` | only with a provider | Server-only credential |
| `REDIS_URL` | no | Reserved for a future cache/rate-limit store |
| `OBJECT_STORAGE_*` | no | Reserved for media storage (Phase 7) |
| `NEXT_PUBLIC_API_BASE_URL` | no | Browser-visible API base URL, no secrets |
| `NEXT_PUBLIC_WEB_BASE_URL` | no | Browser-visible web base URL, no secrets |

Settings are validated at startup. Outside `local`/`ci` the API refuses to
boot with the placeholder `SESSION_SECRET` or without a `DATABASE_URL`.

## Commands

### API

```bash
cd api
uv run python -m app --reload        # start with auto-reload
uv run ruff check .                  # lint
uv run ruff format --check .         # formatting
uv run mypy app                      # type check (strict)
uv run pytest                        # unit tests
uv run pytest -m integration         # database tests (needs DATABASE_URL)
uv run pytest --cov=app --cov-report=term-missing
uv run pip-audit                     # dependency security audit
```

### Web

```bash
cd web
pnpm dev                             # development server
pnpm build && pnpm start             # production build and server
pnpm lint                            # ESLint
pnpm typecheck                       # tsc --noEmit
pnpm test                            # Vitest
pnpm test:coverage                   # Vitest with coverage
pnpm format                          # Prettier
pnpm audit --prod --audit-level=high # dependency security audit
```

### Database

Alembic arrives in Phase 1; the intended commands and the rules are in
[`docs/runbooks/migrations.md`](docs/runbooks/migrations.md).

## Repository layout

```text
/
├── api/                 FastAPI service
│   ├── app/core/        config, logging, errors, middleware, event loop
│   ├── app/api/v1/      HTTP routes
│   └── tests/           unit and integration tests
├── web/                 Next.js 16 application
│   ├── src/app/         routes, including the [locale] segment
│   ├── src/i18n/        locale catalog, routing, request configuration
│   ├── src/lib/         API clients
│   ├── messages/        fixed UI message catalogs (en, ar, de)
│   └── tests/          Vitest tests
├── docs/
│   ├── architecture/    overview and flows
│   ├── decisions/       ADRs
│   └── runbooks/        local development, migrations, backup, incidents
└── .github/workflows/   CI
```

## Quality gates

The same commands run locally and in CI (`.github/workflows/ci.yml`):

| Gate | Command |
| --- | --- |
| API lint / format | `uv run ruff check .` / `uv run ruff format --check .` |
| API types | `uv run mypy app` |
| API tests | `uv run pytest` (+ `-m integration` against PostgreSQL 18) |
| API security | `uv run pip-audit` |
| Web lint | `pnpm lint` |
| Web types | `pnpm typecheck` |
| Web tests | `pnpm test` |
| Web build | `pnpm build` |
| Web security | `pnpm audit --prod --audit-level=high` |

## Decisions

The architecture decisions live in [`docs/decisions/`](docs/decisions/):

1. [Authentication and sessions](docs/decisions/0001-authentication-sessions.md)
2. [Database access style](docs/decisions/0002-database-access-style.md)
3. [Locale routing](docs/decisions/0003-locale-routing.md)
4. [Content storage](docs/decisions/0004-content-storage.md)
5. [Translation provider strategy](docs/decisions/0005-translation-provider.md)
6. [Background jobs and queue](docs/decisions/0006-background-jobs.md)
7. [Toolchain and versions](docs/decisions/0007-toolchain.md)
8. [Media storage](docs/decisions/0008-media-storage.md)

The requirements and the roadmap remain in
[`PROJECT_SPEC.md`](PROJECT_SPEC.md), which is the source of truth.
