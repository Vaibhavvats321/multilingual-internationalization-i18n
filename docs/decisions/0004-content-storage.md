# ADR 0004 — Content storage

- **Status:** Accepted
- **Date:** 2026-10-21
- **Scope:** Where event content and translations live, rich text, versioning

## Context

The platform stores two kinds of text (spec §4.1):

- **Fixed UI strings** of the shared application — "Save", "Sign in",
  validation messages. They belong to the application, not to an event.
- **Dynamic event content** — titles, section text, speaker descriptions,
  registration labels, e-mail templates. They belong to an event, are
  authored by organizers, are translated, and go through a review and
  publish lifecycle.

The data model must support independent translation workflows per entity,
source-revision tracking and published/draft separation, and it must not
force a schema migration when a new locale is enabled (spec §4.2).

## Decision

**Fixed UI strings live in version-controlled message catalogs. Dynamic
content lives in normalised PostgreSQL tables, one row per
(entity, locale, field).**

1. **Fixed UI strings** are JSON message catalogs per locale under
   `web/messages/{locale}.json`, loaded by next-intl. They are translated at
   development time, never at request time, and are covered by a
   key-parity test (`web/tests/messages.test.ts`) that fails when a locale
   is missing a key or contains an empty message.
2. **Dynamic content** uses relational tables, not one large JSON document:
   - `events` — owner, stable slug, dates, timezone, status, default locale,
     published revision.
   - `event_locales` — `(event_id, locale)` with the enablement and publish
     state. A new locale is a row, not a migration.
   - `event_pages` / `event_sections` — stable structure and ordering, with
     no text columns.
   - `event_content_translations` — `(entity_type, entity_id, locale, field,
     source_revision, value, state)`. One row per translatable field per
     locale, with a unique constraint on that tuple and an index on
     `(entity_type, entity_id, locale, state)`.
   - `registration_field_definitions` and
     `registration_field_translations` — stable field IDs with locale
     specific labels, so registrations are never keyed by translated text.
   - `event_theme_settings` — shared style tokens, not translated.
3. **Rich text is stored as structured content**, not as a blob of HTML.
   The safe subset for Phase 1 is a plain-text-with-markdown field that is
   rendered to a **sanitised allowlist** on output. Arbitrary HTML is not
   stored raw. Rendering happens in the web tier with a sanitiser whose
   allowlist is covered by tests.
4. **The source revision is a hash of the source content** (entity, field
   and value). A translation stores the revision it was produced from, so a
   change to the source marks the translation `outdated` without deleting
   the organizer's edits.
5. **Publication is a separate step.** Draft, review, approved and published
   states are stored per row. Public read paths filter on
   `state = 'published'` and on the event's published revision. A public
   endpoint can never return a draft.
6. **JSONB is used only where the shape is genuinely flexible**, namely
   theme settings and the payload of a translation job result. It is not
   used for the translatable content itself, because that needs joins,
   filters and an independent workflow.
7. **Stored text is data, never a key.** Slugs, permissions, field IDs and
   job idempotency keys never contain translated text.

## Alternatives considered

| Alternative | Why it was rejected |
| --- | --- |
| One JSONB column per event holding all content | Simple to write, but a single blob cannot be filtered, reviewed or published per locale, and it makes "which translations are missing" a full-document scan. Spec §4.5 explicitly warns against it. |
| One row per entity and locale with all fields in columns | Fewer rows, but adding a translatable field becomes a migration and the per-field workflow (missing/outdated) becomes awkward. |
| Storing rendered HTML | XSS risk and no way to re-render when the source changes. |
| Storing translations in the same table as the source content | Source and translation have different lifecycles, states and review requirements. |
| Storing fixed UI strings in the database | Spec §4.1 requires them to be version-controlled and never translated per request. |
| Storing translations in a document store (MongoDB) | The workload is relational (joins, integrity, ordered sections) and PostgreSQL is already the platform decision. |

## Consequences

- Queries for a published page join content rows per locale. The indexes
  listed in §2 keep this a bounded number of queries; N+1 patterns are
  forbidden.
- Adding a translatable field means adding a column to the translation
  table (or a new entity type), which is a normal migration, and it never
  requires a per-event data change.
- Completeness checks ("is this locale publishable?") are relational
  queries, which is what the organizer UI needs.
- The sanitiser and its allowlist become security-relevant code and must be
  reviewed and tested.
- The translation table is the largest table in the system; partitioning by
  event is an option if the row counts justify it later.

## Implementation status

Phase 0: the fixed UI catalogs and their parity test exist. The dynamic
content tables are implemented in Phase 1 and Phase 4.
