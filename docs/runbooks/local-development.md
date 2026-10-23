# Local development setup

This runbook brings a clean checkout to a running development stack.

## Prerequisites

| Tool | Version | Check |
| --- | --- | --- |
| Python | 3.13.x | `python --version` |
| uv | 0.12.x | `uv --version` |
| Node.js | 22.23.2 (22 LTS) | `node --version` |
| pnpm | 10.26.2 | `pnpm --version` |
| PostgreSQL | 18 | `psql --version` |

Node 22.23.2 is not cosmetic: `jsdom@30.1.3` declares the engine range
`^22.22.2 || ^24.15.0 || >=26.0.0` and its dependency `undici@8.12.3` uses
the zlib zstd API that only exists from Node 22.15.0. On older 22.x
releases every Vitest worker crashes while loading `undici`. The version is
pinned in `.nvmrc` and in `web/package.json` (`engines`).

## 1. Clone and configure

```bash
git clone <repository-url>
cd MultiLinguaLEventProject
cp .env.example .env
```

Edit `.env` and generate a session secret:

```bash
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

Paste the result into `SESSION_SECRET` in `.env`. `.env` is git-ignored and
must never be committed. The placeholder value is rejected outside `local`
and `ci`.

## 2. Start PostgreSQL

Either with Docker (if available):

```bash
docker compose up -d postgres
```

or with a native PostgreSQL 18 installation:

```bash
createdb -U postgres multilingua
createdb -U postgres multilingua_test
```

Then set `DATABASE_URL` in `.env` accordingly:

```dotenv
# Docker Compose
DATABASE_URL=postgresql://multilingua:multilingua@localhost:5432/multilingua
# Native PostgreSQL with trust authentication
DATABASE_URL=postgresql://postgres@localhost:5432/multilingua
```

`compose.yaml` starts **PostgreSQL only**. The API and the web application
run natively.

## 3. Install the dependencies

```bash
cd api
uv sync --frozen --all-groups

cd ../web
pnpm install --frozen-lockfile
```

Use `--frozen` so that a stale lockfile fails loudly instead of silently
resolving new versions.

## 4. Run the API

```bash
cd api
uv run python -m app --reload
```

The API listens on <http://localhost:8000>.

- `GET http://localhost:8000/api/v1/health/live` → `200` with the service
  name and version.
- `GET http://localhost:8000/api/v1/health/ready` → `200` when PostgreSQL is
  reachable, `503` otherwise.
- `GET http://localhost:8000/api/v1/openapi.json` → the OpenAPI document.

Do not start the API with a bare `uvicorn app.main:app` on Windows: uvicorn
creates a `ProactorEventLoop` before the application is imported and psycopg
rejects it with
`InterfaceError: Psycopg cannot use the 'ProactorEventLoop' to run in async mode.`
`python -m app` selects the selector loop factory
(`api/app/core/event_loop.py`) and avoids the error. See ADR 0002.

## 5. Run the web application

```bash
cd web
pnpm dev
```

The web application listens on <http://localhost:3000>.

- <http://localhost:3000/en>, `/ar` and `/de` render the platform shell.
- `GET http://localhost:3000/api/health/live` → `200`.
- `GET http://localhost:3000/api/health/ready` → `200` when the API is
  reachable, `503` otherwise.

`NEXT_PUBLIC_API_BASE_URL` must point at the API. The shell page itself is
statically rendered and does not need the API at build time; the live API
status is fetched in the browser through `/api/health/ready`.

## 6. Verify the quality gates

```bash
cd api
uv run ruff check .
uv run ruff format --check .
uv run mypy app
uv run pytest                       # unit tests
uv run pytest -m integration        # needs DATABASE_URL

cd ../web
pnpm lint
pnpm typecheck
pnpm test
pnpm build
```

The integration tests are skipped when `DATABASE_URL` is not set. Point them
at the test database, not at the development database:

```dotenv
DATABASE_URL=postgresql://postgres@localhost:5432/multilingua_test
```

## 7. Troubleshooting

| Symptom | Cause | Fix |
| --- | --- | --- |
| `Psycopg cannot use the 'ProactorEventLoop'` | The API was started without the event loop factory | Start it with `uv run python -m app` |
| Vitest crashes in `undici` | Node is older than 22.22.2 | Install Node 22.23.2 (`.nvmrc`) |
| `psycopg` cannot connect | PostgreSQL is not running or the port is wrong | Check `pg_isready` and `DATABASE_URL` |
| `/api/v1/health/ready` returns 503 | The database is unreachable | The detail names the failing dependency, never the credentials |
| The API refuses to start outside `local`/`ci` | Placeholder `SESSION_SECRET` or missing `DATABASE_URL` | Set a real secret and the connection string |
| CORS errors in the browser | The web origin is not allowed | Add the origin to `CORS_ORIGINS` (comma separated) |
