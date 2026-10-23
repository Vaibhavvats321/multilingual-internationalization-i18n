# Backup and restore

Phase 0 does not yet contain user data, but the backup policy is decided now
so that it is not improvised when there is.

## What must be backed up

| Store | Content | Method |
| --- | --- | --- |
| PostgreSQL | Events, content, translations, registrations, sessions, job queue | `pg_dump` (custom format) + WAL archiving |
| Media storage | Images and documents (metadata lives in PostgreSQL) | Object-storage versioning / replication |
| Configuration | `.env` values of the deployment | Secret manager, not the backup volume |

A database backup alone is **not** a complete restore: the media bytes live
outside PostgreSQL (ADR 0008). Both must be restored together.

## Backup policy

- **Full logical backup** nightly, retained for 14 days.
- **Continuous WAL archiving** with a retention of at least 7 days, so a
  point-in-time restore is possible between full backups.
- **Restore drill** every quarter: restore into a scratch environment and
  verify the data. A backup that was never restored is not a backup.
- Backups are encrypted at rest and are not stored in the same failure
  domain as the primary database.

## Logical backup

```bash
# Full dump, custom format (compresses, supports selective restore)
pg_dump --format=custom --file=multilingua_$(date +%Y%m%d_%H%M%S).dump "$DATABASE_URL"

# Verify the archive is readable before trusting it
pg_restore --list multilingua_20261021_210000.dump | head -20
```

## Restore

```bash
# 1. Stop the writers (API and worker), keep the database running.
# 2. Restore into a fresh database.
createdb -U postgres multilingua_restore
pg_restore --dbname=multilingua_restore --no-owner --exit-on-error multilingua_20261021_210000.dump

# 3. Point the application at the restored database and verify.
#    - GET /api/v1/health/ready  -> 200
#    - run the integration test suite against the restored database
#    - spot-check a published event in every enabled locale

# 4. Only then switch DATABASE_URL over to the restored database and
#    restart the API and the worker.
```

## Point-in-time recovery

```bash
# Recover to a specific moment using the WAL archive.
pg_ctl -D "$PGDATA" stop
cp -r /var/lib/postgresql/wal_archive/* "$PGDATA/pg_wal/"
# set restore_command in postgresql.conf, create recovery.signal
# and set recovery_target_time = '2026-10-21 18:00:00+00'
pg_ctl -D "$PGDATA" start
```

## Partial restore (one event)

For a single deleted or corrupted event, restore into a scratch database and
copy the affected rows with `INSERT ... SELECT`, keeping the ids intact so
that registrations and content relationships stay consistent. Every partial
restore is written down in the audit log.

## Verification after every restore

- [ ] Row counts of the main tables match the expected volume.
- [ ] A published event renders in every enabled locale.
- [ ] Registration records are intact and reference existing events.
- [ ] The session table has been cleared or is intentionally preserved.
- [ ] The job queue contains no stale `running` job from before the outage
      (the lease sweeper handles this; check that it ran).

## Secrets

Backup archives contain session hashes and attendee data. Treat them as
sensitive: restrict access, encrypt them, and delete them according to the
retention policy.
