# ADR 0007 — Toolchain, versions and local development

- **Status:** Accepted
- **Date:** 2026-10-21
- **Scope:** Languages, package managers, dependency pinning, containers, CI

## Context

The project is new. The versions of the languages, frameworks and tools are
chosen once at the start and pinned in lockfiles (spec §3.3), so that every
developer and every CI run produces the same result.

The development machine is **Windows**. Docker and WSL are not available on
it, which shapes how the local development stack is assembled.

## Decision

### Languages and package managers

| Concern | Choice |
| --- | --- |
| Backend language | Python **3.13** (`.python-version`: `3.13`) |
| Backend package manager | **uv** with a committed `uv.lock` |
| Frontend language | TypeScript **5.9.3** (`.nvmrc`: `22.23.2`) |
| Frontend runtime | Node.js **22 LTS** |
| Frontend package manager | **pnpm 10** with a committed `pnpm-lock.yaml` |

The root `package.json` pins `"packageManager": "pnpm@10.26.2"` so that
Corepack selects the right pnpm.

### Pinned dependency versions

The versions are listed in `api/pyproject.toml`, `api/uv.lock`,
`web/package.json` and `web/pnpm-lock.yaml`. Notable pins and the reason
for them:

- **TypeScript 5.9.3, not 7.x.** TypeScript 7 is the native port; the
  `typescript-eslint@8.72.0` release used by `eslint-config-next` declares a
  peer range of `<6.1.0`, so TypeScript 7 would break the lint gate.
- **`httpx2` instead of `httpx`.** Starlette 1.9.0 deprecates the `httpx`
  package in favour of `httpx2`; the API test client uses `httpx2` to avoid
  a deprecation warning being raised as an error (`filterwarnings = ["error"]`).
- **Node 22.23.2, not 22.14.0.** `jsdom@30.1.3` declares the engine range
  `^22.22.2 || ^24.15.0 || >=26.0.0`, and its dependency `undici@8.12.3`
  requires Node `>=22.19.0` and uses the zlib zstd API that only exists
  from Node 22.15.0. On Node 22.14.0 every Vitest worker crashed while
  loading `undici`. The CI job pins the same major.
- **PostgreSQL 18** for the local database and the CI service container.

### Local development stack

- `compose.yaml` provides **PostgreSQL only** (`postgres:18-alpine`), with
  a health check, a named volume and the database `multilingua`. The API
  and the web application run **natively** on the host, which keeps the
  edit-reload loop fast and works on machines without Docker.
- The API is started with `uv run python -m app --reload`, which also
  applies the selector event loop required by psycopg on Windows
  (ADR 0002).
- The web application is started with `pnpm dev`.
- A second database `multilingua_test` exists for the integration tests.
- `.env.example` documents every variable; the real `.env` is
  git-ignored and contains local values only.

### Quality gates

- **API:** `ruff check`, `ruff format --check`, `mypy app`, `pytest`
  (unit tests always, integration tests when `DATABASE_URL` is set).
- **Web:** `eslint .`, `tsc --noEmit`, `vitest run`, `next build`.
- **Security:** `pip-audit` for Python, `pnpm audit` for the web
  application.
- All gates run in **GitHub Actions** (`.github/workflows/ci.yml`) with the
  pinned tool versions and a PostgreSQL service container.

## Alternatives considered

| Alternative | Why it was rejected |
| --- | --- |
| Docker Compose for the whole stack | Docker is not available on the development machine, and bind-mounted source and hot reload complicate the first setup. |
| npm or Yarn for the frontend | pnpm's strict, content-addressed store makes the lockfile deterministic and installs faster; Yarn Classic is unmaintained. |
| Poetry for the backend | uv resolves and installs considerably faster and the lockfile is a single readable file. |
| The latest TypeScript release | Broken peer requirements with the current ESLint stack. Stability of the toolchain is preferred over novelty. |
| Pre-commit hooks as the only gate | Hooks are easy to skip and are not reproducible on CI; the same commands run in CI. |
| A self-hosted CI runner | No need in the first phase; GitHub Actions is free for this workload. |

## Consequences

- Every developer needs Node 22.23.2, Python 3.13, uv and pnpm 10. The
  versions are documented in the README and pinned in `.nvmrc` and
  `.python-version`.
- Lockfiles are committed and must be regenerated only intentionally; CI
  runs `pnpm install --frozen-lockfile` and `uv sync --frozen`.
- Upgrades are separate, reviewed changes: bump the version, regenerate the
  lockfile, run the gates.
- The web application requires a reachable API for the readiness proxy, but
  the shell page and the build do not.

## Implementation status

Phase 0: implemented. The versions above are the ones in the committed
lockfiles.
