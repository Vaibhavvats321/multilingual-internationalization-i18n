# Incident response

The procedures below are the starting point for handling a production
incident. They are deliberately short: an incident is a bad time to read a
long document.

## Severity

| Level | Definition | Response |
| --- | --- | --- |
| SEV 1 | The public site is down or publishing wrong content | Immediate, 24/7 |
| SEV 2 | A core feature is broken for a subset of users, or the API is degraded | Within 1 hour |
| SEV 3 | A non-critical feature is broken | Next working day |

## First 15 minutes

1. **Confirm the impact.** Which endpoints fail, for whom, since when?
   Compare `/api/v1/health/ready` and the web readiness probe.
2. **Check the obvious dependencies**: PostgreSQL reachable? Disk space? A
   recent migration or deployment?
3. **Look at the logs** of the failing service. Every request carries an
   `X-Request-ID`; the same id is in the structured logs.
4. **Stop the bleeding** before diagnosing: roll back the last deployment,
   disable the failing feature, or fail over to the previous version.
5. **Do not** run destructive database operations, delete data or change
   production configuration during the first pass.

## Known failure modes and the first action

| Symptom | Likely cause | First action |
| --- | --- | --- |
| `/api/v1/health/ready` returns 503 | PostgreSQL is unreachable or saturated | Check `pg_isready`, connection count, slow queries |
| The API returns 5xx with `InterfaceError` | The process was started without the selector event loop (Windows) | Restart with `python -m app`; see ADR 0002 |
| The public page shows a draft or the wrong locale | A publish bug or a cache mix-up | Purge the cache; compare the published revision |
| Translation jobs stay `pending` | The worker is down or the queue is stuck | Check the worker process and the oldest pending job age |
| A provider outage | The provider is failing | Jobs fail with a safe error; the site is unaffected. Manual translation remains available |
| 4xx floods on one endpoint | Abuse or a misbehaving client | Apply rate limiting, review the logs, block if necessary |
| CORS errors in the browser | `CORS_ORIGINS` no longer matches the deployment origin | Fix the configuration and restart the API |

## Diagnostics

```bash
# Application health
curl -i http://localhost:8000/api/v1/health/live
curl -i http://localhost:8000/api/v1/health/ready
curl -i http://localhost:3000/api/health/ready

# Database
pg_isready -h localhost -U postgres
psql -c "select state, count(*) from pg_stat_activity group by state;"
psql -c "select pid, now() - query_start as runtime, query from pg_stat_activity where state = 'active' order by runtime desc limit 10;"
psql -c "select count(*) from translation_jobs where state = 'pending';"
```

## After the incident

1. Write the timeline: detection, mitigation, resolution.
2. Restore the normal state: remove temporary mitigations, re-enable
   features, clear stale queue entries.
3. Verify the system end to end: health endpoints, one published event per
   locale, one registration flow.
4. Document the follow-up work. A repeat incident is a process problem, not
   only a bug.
5. Never include secrets, tokens or attendee data in the incident report.

## Communication

- The public statement says what is affected and what the workaround is; it
  does not expose internals.
- Internal updates carry the timeline and the next action, not speculation.
