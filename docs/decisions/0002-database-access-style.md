# ADR 0002 — Database access style

- **Status:** Accepted
- **Date:** 2026-10-21
- **Scope:** PostgreSQL access from the API, driver choice, event loop constraints

## Context

The API serves public event pages and organizer operations. Read traffic is
dominated by page rendering, while translation jobs and notification sending
(Phases 5 and 6) are long-running and must not block request handling.

The decisions in this ADR affect every module that touches the database and
therefore cannot be deferred to the first query.

## Decision

**Async SQLAlchemy 2.0 with the psycopg 3 driver.**

1. All database access uses **async** SQLAlchemy 2.0 sessions
   (`AsyncSession`, `create_async_engine`) over the `postgresql+psycopg`
   dialect.
2. The driver is **psycopg 3** (`psycopg[binary]`). psycopg 3 supports both
   sync and async APIs; only the async API is used.
3. **Alembic** owns the schema. Migrations are reviewed and applied
   explicitly; the application never runs migrations on startup.
4. One session per request, provided by a FastAPI dependency that commits on
   success and rolls back on error. No session is shared between requests
   and no session is held open across an external call.
5. The connection pool is sized for the deployment (`pool_size`,
   `max_overflow`) and every statement has a statement timeout so a slow
   query cannot exhaust the pool.
6. All queries use bound parameters. String interpolation into SQL is
   forbidden, including for identifiers (dynamic identifiers are selected
   from an allow-list).
7. **External calls happen outside database transactions.** A translation
   provider call or an email send must not happen while a transaction is
   open.

### Windows event loop constraint

psycopg's async implementation requires a `SelectorEventLoop`. On Windows,
`asyncio.ProactorEventLoop` is the default and psycopg raises
`InterfaceError: Psycopg cannot use the 'ProactorEventLoop' to run in async
mode.`

uvicorn 0.54 creates the event loop *before* the application module is
imported, so an event loop policy installed at import time is too late. The
API therefore ships an explicit loop factory
(`api/app/core/event_loop.py::selector_loop_factory`) and starts uvicorn
through `api/app/__main__.py` with
`loop="app.core.event_loop:selector_loop_factory"`. The policy installer
remains available for pytest and other in-process embeddings.

## Alternatives considered

| Alternative | Why it was rejected |
| --- | --- |
| Synchronous SQLAlchemy with psycopg 3 | Synchronous drivers block the event loop. With FastAPI's threadpool this works, but it wastes threads under load and blocks the background work the roadmap requires. |
| SQLAlchemy + asyncpg | asyncpg is fast, but psycopg 3 is the reference implementation for PostgreSQL, supports SCRAM/SSPI authentication and modern protocol features, and keeps the dependency surface smaller. |
| Raw psycopg 3 without an ORM | The data model in spec §4.5 is relational with joins, integrity constraints and per-table workflows. Hand-written SQL for every module would add cost without removing the need for a migration tool. |
| Tortoise ORM / peewee | Smaller ecosystems, weaker async story and less explicit transaction control than SQLAlchemy 2. |
| An ORM per service with its own database | Breaks the "one shared application" model and multiplies migration coordination. |

## Consequences

- The async API is mandatory; a blocking call inside a request handler
  blocks the whole worker. Static analysis and review must watch for it.
- The event loop factory is a hard requirement on Windows and must be
  preserved in any change to the start-up path. A regression test
  (`api/tests/test_event_loop.py`) covers it.
- Async requires careful transaction scoping: sessions are short-lived and
  never span an `await` on a third-party service.
- `pytest-asyncio` runs the async tests; the database integration tests are
  marked `integration` and are skipped when no `DATABASE_URL` is configured.

## Implementation status

Phase 0: the driver, the configuration and the health probe are in place.
SQLAlchemy, Alembic and the repositories are Phase 1, as stated in spec §10.
