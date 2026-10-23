# Architecture overview

Phase 0 description of the platform. It documents the shape that the later
phases implement, and it is written against `PROJECT_SPEC.md` and the
decisions in `docs/decisions/`.

## Components

| Component | Technology | Responsibility |
| --- | --- | --- |
| Web application | Next.js 16 (App Router), React 19, TypeScript | Public event websites, organizer dashboard, locale routing, fixed UI strings |
| API | FastAPI, Python 3.13 | Domain logic, authorization, content and translation persistence, health endpoints |
| Database | PostgreSQL 18 | Events, locales, content, translations, registrations, sessions, job queue |
| Worker | Python process | Background work: translation jobs, e-mail, cleanups (Phase 5+) |
| Object storage | S3-compatible (adapter) | Media bytes; metadata stays in PostgreSQL (Phase 7) |

There is **one** web application and **one** API serving **many** event
websites. Isolation between organizers comes from ownership and
authorization in the data model, not from separate deployments
(spec §15).

```
                    ┌──────────────────────┐
   browser  ───────▶│  web (Next.js 16)    │
                    │  /{locale}/events/…  │
                    └──────────┬───────────┘
                               │ HTTP/JSON (same-origin proxy for health)
                               ▼
                    ┌──────────────────────┐
                    │  api (FastAPI)       │
                    │  /api/v1/…           │
                    └──────┬────────┬──────┘
                           │        │ enqueue
                           ▼        ▼
                    ┌────────────┐  ┌──────────────┐
                    │ PostgreSQL │  │ worker       │
                    │ + job queue│  │ (Phase 5+)   │
                    └────────────┘  └──────────────┘
```

## Repository layout

```
/
├── api/            FastAPI service (app/, tests/, pyproject.toml, uv.lock)
├── web/            Next.js application (src/, messages/, tests/)
├── docs/           architecture/, decisions/, runbooks/
├── compose.yaml    PostgreSQL only
└── .github/        CI workflows
```

## Request flow

### Public event page

1. The browser requests `/{locale}/events/{slug}`.
2. The Next.js proxy (`web/src/proxy.ts`, next-intl) resolves the locale and
   redirects a request without a prefix to the best matching locale.
3. The route renders the page. The content comes from the API, which returns
   **published** content for **published** locales only.
4. The API validates ownership/publication state and returns the content for
   the requested locale; drafts are never included.
5. The page renders with the `dir` attribute and the date/number formats
   derived from the locale.

Only the requested locale is rendered. A locale switch links to the same
route in another locale; an unpublished locale falls back to the event's
default locale (ADR 0003).

### Organizer request

1. The browser calls the API under `/api/v1` with the session cookie.
2. The API resolves the session (SHA-256 lookup of the cookie token) and
   loads the user.
3. Authorization is checked **on the server** for the concrete resource.
   The web application only reflects the result in the UI.
4. State-changing requests additionally require a matching
   `X-CSRF-Token` header (double-submit, ADR 0001).

### Health and probes

| Endpoint | Meaning | Failure behaviour |
| --- | --- | --- |
| `GET /api/v1/health/live` | The API process is alive | Never depends on the database |
| `GET /api/v1/health/ready` | The API can serve traffic (database reachable) | `503` with a redacted detail |
| `GET /api/health/live` | The web process is alive | Never depends on the API |
| `GET /api/health/ready` | The web process can serve traffic (API reachable) | `503` |

The liveness probe never depends on a downstream service, so an outage of
PostgreSQL does not cause a restart loop of healthy processes.

## Data flow

### Writing content

```
organizer UI ──▶ api ──▶ events / event_locales / event_content_translations
                        └─▶ translation_jobs (enqueue, never inline)
```

Rules that hold for every write:

- One transaction per request; the session is opened and closed per request.
- External calls (provider, e-mail) happen **outside** the transaction.
- The source revision of a translation is the hash of the source content.
  A changed source marks the translation `outdated`; the organizer's edits
  are preserved.

### Reading published content

```
browser ──▶ web ──▶ api ──▶ published revision + published locale rows
```

The public read path filters on `state = 'published'` and on the event's
published revision. Draft and review content is never returned by a public
endpoint and never shares a cache entry with published content.

### Translating

```
event content changed
   └─▶ translation_jobs row (idempotency key: event+locale+source revision+scope)
          └─▶ worker claims job (FOR UPDATE SKIP LOCKED)
                 └─▶ provider adapter (timeout, bounded retries, rate limit)
                        └─▶ draft translation rows (source untouched)
                               └─▶ organizer review ──▶ publish
```

## Cross-cutting concerns

- **Configuration** is validated once at startup (`api/app/core/config.py`).
  Missing production secrets fail the boot, not the first request.
- **Logging** is structured JSON via structlog. Secrets are redacted; the
  request id links the log entries of one request.
- **Errors** use one envelope: `{"error": {"code", "message", "details",
  "request_id"}}`. Unexpected exceptions are logged server-side with a
  generic message returned to the client.
- **Security**: server-side authorization on every request, `HttpOnly`
  session cookie, CSRF double-submit, bound SQL parameters only, sanitised
  rich text, no provider credentials on the client.
- **Observability** starts with the health endpoints, the request id and
  structured logs. Metrics and tracing are Phase 7.

## References

- `docs/decisions/0001-authentication-sessions.md`
- `docs/decisions/0002-database-access-style.md`
- `docs/decisions/0003-locale-routing.md`
- `docs/decisions/0004-content-storage.md`
- `docs/decisions/0005-translation-provider.md`
- `docs/decisions/0006-background-jobs.md`
- `docs/decisions/0007-toolchain.md`
- `docs/decisions/0008-media-storage.md`
