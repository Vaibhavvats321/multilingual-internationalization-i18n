# ADR 0006 — Background jobs and queue

- **Status:** Accepted
- **Date:** 2026-10-21
- **Scope:** Translation jobs, e-mail sending, background processing

## Context

Several parts of the roadmap must not run inside a request: translation
provider calls, e-mail delivery, scheduled cleanups (expired sessions,
outdated translation detection) and eventually media processing.

Phase 0 does not run any worker, but the storage and the trigger mechanism
must be decided before the first job is implemented, because the design
determines whether a job survives a restart and whether it can be retried
safely.

Constraints that shaped the decision:

- The project must be runnable locally with **one** service (`compose.yaml`
  currently provides PostgreSQL only).
- No Redis is running and none should be required for Phase 0 or Phase 1.
- Jobs must be observable: an organizer must be able to see that a
  translation job failed and why.

## Decision

**PostgreSQL as the job queue. A worker process polls the queue with
`SELECT ... FOR UPDATE SKIP LOCKED`.**

1. **`translation_jobs` (and later `outbox_events`) is the queue.** A job
   row carries `state` (`pending`, `running`, `succeeded`, `failed`,
   `retrying`), `attempts`, `run_at`, `idempotency_key`, `payload` (JSONB)
   and safe error metadata. The payload never contains credentials.
2. **A dedicated worker process claims jobs** with
   `SELECT ... FROM translation_jobs WHERE state = 'pending' AND run_at <= now() ORDER BY run_at FOR UPDATE SKIP LOCKED LIMIT 1`.
   `SKIP LOCKED` allows several workers to run without a broker and without
   double execution.
3. **Redis is not introduced now.** It is added only when a measurement
   shows that polling latency or write contention is a problem. The
   alternative is recorded in `REDIS_URL`, which stays unset.
4. **Idempotency keys prevent duplicate work.** The key is
   `(event_id, locale, source_revision, scope)` and is enforced by a unique
   index, so enqueueing the same translation twice is a no-op.
5. **Retries use exponential backoff with a bounded attempt count.** Each
   failure updates `attempts` and `run_at`. After the bound is reached the
   job moves to `failed` with a safe error summary, and the organizer can
   retry it explicitly.
6. **A job lease prevents stuck jobs.** A `running` job whose lease expired
   (worker died) is returned to `pending` by a periodic sweeper, so a crash
   does not silently lose work.
7. **The API never performs the work itself.** It enqueues and returns a job
   identifier; the organizer UI polls the job status. The public site never
   waits for a job.
8. **The worker is a separate process** (`python -m app.worker` in Phase 5)
   and is started independently of the API in every environment.
9. **Job payloads are validated before execution** and provider credentials
   are read from the environment at call time, never stored in the queue.

## Alternatives considered

| Alternative | Why it was rejected |
| --- | --- |
| Celery with Redis or RabbitMQ | Adds a broker, a second configuration surface and an operational dependency in the first phase, for a workload that is not yet throughput-bound. |
| Run the job inline in the request | Blocks the request on a rate-limited external call and makes failures visible to public users (spec §4.3). |
| `pg_cron` / database triggers | Good for simple scheduled work, but they cannot run Python provider adapters with retries and backoff. |
| An external task service (SQS, SQS-compatible) | Adds cloud coupling and local development friction before the need is proven. |
| A dedicated message broker (RabbitMQ) | More operational weight than the problem justifies; the database queue is sufficient at the expected scale. |
| In-process `asyncio` task queue | Work is lost on restart and provides no shared state between API instances. |

## Consequences

- The API needs a database and the worker needs the same database. That is
  an acceptable trade: it is one component to run locally.
- Queue latency is bounded by the poll interval (a few seconds). For
  interactive features the API returns a job id and the UI polls.
- `SELECT ... FOR UPDATE SKIP LOCKED` requires PostgreSQL 9.5+; the project
  targets PostgreSQL 18.
- The queue tables need careful indexing and must be monitored for the
  oldest pending job age.
- If the queue later needs to move to Redis or a broker, the job table
  remains the source of truth for job state, so the migration is additive.

## Implementation status

Phase 0: `TRANSLATION_PROVIDER` and `REDIS_URL` exist as configuration
names only, with the defaults documented in `.env.example`. The queue
tables and the worker arrive in Phase 5.
