# Database migrations

Phase 0 does not run migrations: Alembic and SQLAlchemy are Phase 1
(spec §10). This runbook documents the rules that apply from the first
migration and the commands the project will use.

## Principles

1. **The application never migrates on startup.** Migrations are applied by
   an operator or by a release step, before the new version serves traffic.
2. **Every migration is reviewed.** A migration is code: it ships with the
   change, is reviewed with it, and is tested against a copy of production
   data before release.
3. **Migrations are forward-only.** A failed migration is repaired by a new
   migration, not by editing an applied one. `downgrade` exists for local
   development only; it is not part of the production procedure.
4. **Every migration is reversible or explicitly documented as
   irreversible.** An irreversible migration states in its docstring why and
   what the compensating action is.
5. **No destructive operation without an approved plan.** Dropping a column
   or shrinking a table is split into several releases: stop writing, wait,
   then drop.

## Commands

The commands below are the intended interface once Alembic is added in
Phase 1:

```bash
cd api

# Create a revision from the models
uv run alembic revision --autogenerate -m "add events table"

# Apply everything
uv run alembic upgrade head

# Show the current revision
uv run alembic current

# Show the migration history
uv run alembic history

# Inspect the SQL without applying it
uv run alembic upgrade head --sql
```

## Applying a migration in an environment

1. Take a backup (see `docs/runbooks/backup-and-restore.md`).
2. Apply the migration with a single operator:
   `uv run alembic upgrade head`.
3. Verify: `uv run alembic current` reports the expected revision, and
   `uv run pytest -m integration` passes against the migrated schema.
4. Roll the application forward only after the verification succeeds.
5. Deploy the application code.

## Adding a new locale

Adding a locale to an existing event is a **data** change, not a schema
change: a row in `event_locales` (ADR 0004). No migration is required, and
the event id, slug and registrations do not change.

## Schema review checklist

- [ ] The migration is in the same change as the code that needs it.
- [ ] Constraints and indexes match the intended access patterns.
- [ ] `NOT NULL` columns are added with a default or in two steps.
- [ ] No `SELECT *`-style wide rewrites on a large table.
- [ ] The migration was applied and rolled back locally on a copy of
      production data.
- [ ] The downgrade path was tested, or the irreversibility is documented.
