MultiLinguaLEventProject --- Project Source of Truth
File: PROJECT_SPEC.md
Status: Authoritative product and engineering specification
Last updated: 2026-10-22

This document is the primary source of truth for this repository's
product scope, architecture, internationalization, engineering
standards, roadmap, and acceptance criteria.
Repository boundary: This specification applies only to
C:\Projects\MultiLinguaLEventProject. Do not mix it with any other
project's code, architecture, history, or requirements. Inspect the
actual repository before editing and preserve existing code and data.

1. Product Vision
Build a production-oriented, scalable, multilingual event-management
platform. Organizations should be able to create, publish, manage, and
analyze events for international audiences through an organizer
dashboard and localized public event pages.

The product roadmap may include organization workspaces, event
lifecycle, localized event pages, registration, attendee management,
ticketing, QR check-in, agenda and speakers, communications, analytics,
and future integrations. Implement only the phase explicitly requested;
this roadmap is not permission to build everything at once.
Product principles
1. Internationalization is foundational, not a late-stage UI add-on.
2. Static UI messages and organizer-created event content are separate
   translation layers.
3. Tenant isolation and authorization are mandatory.
4. PostgreSQL is the source of truth for transactional data.
5. Control database load with bounded queries, indexes, pagination,
   short transactions, measured caching, and asynchronous jobs.
6. Start with a modular monolith; avoid premature microservices.
7. Prefer readable, typed, cohesive code and avoid unnecessary
   abstractions/dependencies.
8. A feature is complete only after implementation, tests, and
   verification.
9. Do not claim performance or correctness that has not been measured.
2. Users and Product Modules
User roles
- Platform Administrator: platform settings, tenant status, plans,
  support audit, and system health.
- Organization Owner/Admin: workspace, team, permissions, and
  authorized settings.
- Event Manager: creates, edits, publishes, and operates assigned
  events.
- Event Staff: uses event-scoped check-in and sees only necessary
  attendee data.
- Read-only Analyst: views authorized reports.
- Attendee: views localized event pages and manages their own
  registration.
- Speaker/Exhibitor: future-ready roles for assigned profiles and
  event content.
Product modules (phased)
- Identity, sessions, organizations, memberships, and RBAC.
- Event lifecycle: draft, published, paused, completed, cancelled,
  archived.
- Localized event pages and content.
- Registration, attendee records, capacity controls, and
  confirmations.
- Tickets, QR validation, and check-in.
- Agenda, sessions, speakers, tracks, and venues.
- Email notifications and background jobs.
- Analytics and asynchronous exports.
- Future payments, subscriptions, integrations, and webhooks.
3. Internationalization (i18n) --- Foundational Requirement
3.1 Required approach
Use next-intl with Next.js App Router for frontend
internationalization, after verifying compatibility with the versions
installed in the repository.

Initial supported locales:
- en --- English
- ar --- Arabic
The architecture must allow adding locales through documented
configuration and message files, without rewriting components.

Do not treat a language toggle as complete i18n. Locale routing, static
UI messages, dynamic database content, fallback behavior, metadata,
date/number formatting, and RTL/LTR layout must work together.
3.2 Separate translation layers
A. Static UI translations
Static messages include navigation labels, buttons, forms, validation,
empty states, status labels, notifications, and UI errors.

Rules:
- Store messages in version-controlled locale files, organized by
  feature/namespace when useful.
- Use next-intl APIs compatible with the installed version.
- Do not hardcode user-facing strings in components.
- Avoid duplicating the same message unnecessarily.
- Detect missing translation keys in development/tests.
- Define an intentional fallback policy.
- Do not store static UI strings in PostgreSQL unless a future,
  approved runtime content-management requirement justifies it.
Suggested structure (adapt after inspecting existing files; do not
blindly restructure):
web/
  messages/
    en.json
    ar.json
  src/
    i18n/
      routing.ts
      request.ts
    app/
      [locale]/
        layout.tsx
        page.tsx
B. Dynamic database content
Organizer-created content may include event title, summary, description,
public page sections, session/agenda titles and descriptions, speaker
biographies, FAQs, and event-specific calls to action.

Rules:
- Inspect existing models and migrations before designing the schema.
- Use a normalized translation model or justify another design.
- Use foreign keys, unique constraints, and indexes for translation
  lookup.
- Define event default locale, enabled/published locales, and
  translation completeness.
- Define draft/published translation states if the product workflow
  requires them.
- Keep language-independent data (capacity, event identity,
  timestamps) separate from translated fields unless there is a clear
  reason otherwise.
- Do not store organizer-created content in frontend message JSON
  files.
- Do not fetch every locale when one is requested.
- Do not issue one query per event to fetch translations.
- Do not create a second translation system if a suitable one already
  exists.
3.3 Locale routing
Use locale-prefixed URLs unless the existing repository or an approved
product decision specifies otherwise:
- /en/... --- English
- /ar/... --- Arabic
Requirements:
- Validate locales against explicit configuration.
- Avoid duplicate locale prefixes and redirect loops.
- Define default locale and locale-detection policy.
- Respect a locale explicitly selected by the user.
- Preserve the equivalent page when switching locale if that
  route/translation exists.
- If the equivalent route is unavailable, use a documented fallback
  route and do not imply a translation exists.
- Keep public slugs and locale URL behavior consistent.
- Do not accidentally route API endpoints through locale middleware.
- Test nested routes, unsupported locales, query strings, and
  trailing-slash behavior as applicable.
3.4 Language switcher
- Use accessible language names and keyboard-operable controls.
- Preserve the current page when a corresponding localized route
  exists.
- Preserve relevant query/filter state only when safe and meaningful.
- Fall back predictably when a translated route does not exist.
- Update document language, direction, and localized metadata.
- Do not lose form input unexpectedly during language changes.
3.5 Arabic and RTL
- Set HTML lang and dir from the active locale.
- English uses ltr; Arabic uses rtl.
- Prefer CSS logical properties such as margin-inline-start,
  padding-inline-end, and inset-inline-start.
- Test navigation, sidebars, breadcrumbs, forms, tables, dialogs,
  dropdowns, icons, charts, pagination, and responsive layouts in both
  directions.
- Do not blindly mirror every icon or component.
- Support mixed Arabic/Latin text, email addresses, URLs, numbers, and
  form inputs.
- Use locale-aware date, time, and number formatting.
- Store timestamps in UTC and retain an event's IANA timezone
  identifier.
- Verify Arabic fonts, line height, focus order, keyboard navigation,
  and overflow.
3.6 Missing-translation fallback
Use one documented policy across frontend and backend. Baseline policy:
1. Return the requested locale's published translation when available.
2. Otherwise return the event's configured default-locale translation,
   if available.
3. If neither exists, show a clear unavailable-content state; do not
   fabricate or silently machine-translate content.
Where useful, the API should identify the requested and actually served
locale. Fallback must never bypass publication rules, authorization,
tenant isolation, or visibility rules.
3.7 SEO and metadata
- Localize page title, description, Open Graph metadata, and canonical
  URL.
- Add hreflang only for locale routes that actually exist.
- Verify rendered metadata and avoid misleading canonical URLs or
  duplicate pages.
4. Recommended Technical Architecture
Unless inspection shows a justified existing choice, the recommended
baseline is:
- Frontend: Next.js App Router + TypeScript.
- Frontend i18n: next-intl.
- Backend: FastAPI + Python + Pydantic.
- Database: PostgreSQL.
- Migrations: Alembic.
- Cache/short-lived coordination: Redis only when a concrete need
  justifies it.
- Background work: durable queue and worker when asynchronous
  tasks are introduced.
- Media: object storage/CDN when uploads are implemented; avoid
  large blobs in PostgreSQL.
- API: versioned REST contracts and OpenAPI.
- Operations: structured logs, request IDs, health/readiness
  endpoints, metrics, and error monitoring.
Verify installed versions, current dependencies, environment, and
existing architecture before making changes. Do not add every technology
at once.
Backend boundaries
As the application grows, keep cohesive modules for identity,
organizations, events, event translations, registrations, tickets,
check-in, agenda, communications, analytics, integrations,
subscriptions, and audit. Adapt to the actual repository; do not create
empty modules merely to match a diagram.
Localized request flow
1. Browser requests /en/events/example or /ar/events/example.
2. Next.js validates the locale and loads static UI messages.
3. The page requests event data using the selected locale through the
   existing API contract.
4. FastAPI validates the locale and applies visibility, tenant, and
   authorization rules.
5. PostgreSQL returns the requested published translation and bounded
   fallback data if needed.
6. API returns a typed response and the served locale where relevant.
7. Next.js renders correct messages, lang, dir, and localized
   metadata.
8. Published data may be cached with locale-aware keys and documented
   invalidation.
This is the target flow; inspect existing implementation before changing
it.
5. Database Design and Performance
5.1 Database principles
- PostgreSQL is the source of truth for transactional data.
- Use reviewed Alembic migrations for schema changes.
- Use foreign keys, unique/check constraints, and NOT NULL
  constraints to protect invariants.
- Use UTC timestamps and explicit event timezone identifiers.
- Store money as integer minor units plus currency code, never
  floating-point.
- Use JSONB only for genuinely flexible/versioned payloads; frequently
  queried fields belong in typed columns.
- Define archive/deletion and retention behavior.
- Add indexes based on real access patterns, not indiscriminately.
5.2 Query rules
1. Prevent N+1 queries on list/detail endpoints.
2. Fetch only required columns and the selected locale.
3. Paginate large collections; prefer cursor/keyset pagination for
   high-volume lists.
4. Cap page size, payload size, import size, and export size.
5. Index actual filters, joins, and sort patterns after reviewing query
   plans.
6. Avoid SELECT * on performance-sensitive paths.
7. Never run one query per item in a loop when batching is possible.
8. Avoid counting all historical rows on every request.
9. Do not compute expensive dashboard aggregates on every page load.
10. Keep transactions short; never wait on an external provider while
    holding a transaction.
11. Use bulk writes for imports and batch updates.
12. Avoid over-indexing; indexes have storage and write costs.
13. Size connection pools based on total API/worker replicas and
    database capacity.
14. Set appropriate request, statement, and lock timeouts.
15. Use EXPLAIN (ANALYZE, BUFFERS) in a safe test/staging environment
    for critical queries.
16. Fix inefficient queries before adding cache layers.
5.3 Translation-specific database performance
- Localized lists must not issue one query per event.
- Fetch a page of requested-locale translations in a bounded query or
  a small documented number of queries.
- Index translation lookup keys (for example, resource ID + locale)
  according to the actual schema.
- Enforce uniqueness for one translation per resource/locale unless
  versioning is a documented requirement.
- Fetch only the requested locale and necessary fallback.
- Avoid loading every locale into memory on each request.
- Use locale-aware cache keys including resource identity and
  published version where appropriate.
- Invalidate or version caches after translation publish/update.
- Never let cache entries expose drafts or bypass authorization.
- Document fallback query behavior and keep it bounded.
5.4 Transactions and idempotency
- Use transactions for atomic business operations.
- Use database constraints as the final guard against duplicates.
- Protect capacity and check-in operations against concurrent
  requests.
- Make retry-prone writes idempotent.
- Use an outbox/event pattern when a committed change must reliably
  trigger background work.
- Assume queues and webhooks can deliver duplicates.
- Reconcile derived counters and external provider states where
  needed.
5.5 Caching
For each important cache, document key, TTL, invalidation, tenant/locale
scope, freshness, and fallback. Start with published, read-heavy public
event data when measurement supports it. Do not cache sensitive data or
authorization decisions without a reviewed design. Cache failure must
not cause incorrect permissions or data corruption. Do not add Redis
solely because it is listed here.
6. API Design and Localization
- Keep API routes independent of frontend locale routing unless the
  API contract requires otherwise.
- Select and document one locale-resolution strategy, such as an
  allowlisted query parameter or Accept-Language, including
  precedence. Do not support conflicting methods without a policy.
- Validate locale against supported locales.
- Keep authentication and authorization independent of locale.
- Use typed request/response schemas and a stable error envelope.
- Keep machine-readable error codes stable; display messages may be
  localized.
- Document requested locale, served locale, and fallback where
  relevant.
- Use bounded pagination and allowlisted filters/sorts.
- Apply rate limits, payload limits, and request timeouts to
  appropriate endpoints.
- Keep OpenAPI and frontend API types aligned.
- A locale parameter is never proof of tenant/resource authorization.
7. Security, Privacy, and Tenant Isolation
Tenant isolation
- Every tenant-owned resource must have a clear organization ownership
  path.
- Validate tenant scope in backend services for every protected
  operation.
- Never trust organization/event/user/role IDs from the browser
  without checking the authenticated principal.
- Test cross-tenant reads, writes, searches, exports, translations,
  media access, and background jobs.
- Include tenant scope in cache keys for tenant-owned resources.
- Consider PostgreSQL RLS only if justified by the threat and
  operational models; it does not replace application authorization.
Security baseline
- Use a maintained password-hashing library.
- Use secure sessions/cookies or a reviewed token strategy; protect
  cookie-authenticated writes against CSRF.
- Configure production CORS explicitly.
- Protect against injection, XSS, CSRF, SSRF, brute force, insecure
  direct object references, and mass assignment.
- Validate uploaded file types, sizes, and content.
- Keep secrets out of source control, client bundles, logs, and
  errors.
- Apply least privilege to database, workers, storage, and deployment
  credentials.
- Audit sensitive actions.
- Verify webhooks and make delivery retry-safe when implemented.
Privacy
- Collect only necessary personal data.
- Define retention, deletion, export, and access policies for attendee
  data.
- Do not log credentials, tokens, payment details, full registration
  forms, or unnecessary personal data.
- Use synthetic test data.
- Define consent and unsubscribe behavior before enabling email/SMS
  campaigns.
8. Reliability and Observability
- Maintain separate liveness and readiness endpoints.
- Readiness should reflect whether the service can safely accept
  traffic, including required dependency checks.
- Use graceful shutdown and bounded worker concurrency.
- Use retry limits, exponential backoff, jitter, and dead-letter
  handling for jobs.
- Apply timeouts to external calls and prevent cascading failures.
- Define backup, restore, migration, and incident procedures before
  production.
- Test restore procedures.
- Use structured logs with correlation IDs and no sensitive payloads.
- Monitor route latency, errors, DB pool wait time, slow queries,
  locks, active connections, cache hit rate, queue depth, and oldest
  job age.
- Avoid high-cardinality metric labels such as email addresses, user
  IDs, event IDs, or arbitrary URLs.
9. Frontend Quality and Accessibility
- Use a consistent design system and accessible reusable components.
- Support keyboard navigation, visible focus, semantic labels,
  contrast, and screen-reader feedback.
- Provide loading, empty, success, validation, permission-denied, and
  failure states.
- Avoid loading entire datasets into the browser.
- Debounce search where appropriate and paginate results.
- Keep public event pages responsive and SEO-friendly.
- Use locale-aware date, time, and number formatting.
- Test English LTR and Arabic RTL at supported screen sizes.
- Avoid hardcoded left/right CSS where logical properties work.
- Avoid duplicate API requests and uncontrolled cache invalidation.
- Ensure language switching does not unexpectedly discard form input
  or navigate to an unrelated page.
10. Performance and Scalability Targets
These are goals to validate with representative load tests, not claims
of achieved capacity.
- Warm-cache public event API: target p95 below 300 ms at agreed load.
- Typical authenticated read API: target p95 below 400 ms at agreed
  load.
- Registration/check-in API: target p95 below 500 ms at agreed load,
  excluding external provider delays.
- Target error rate below 1% during the defined steady-state test.
- Avoid database connection saturation and unbounded queue growth.
- Record baseline throughput and p50/p95/p99 latency before claiming
  improvement.
- Test bursts, duplicate requests, cold caches, slow dependencies, and
  DB connection pressure.
- Measure query count/latency for localized event list and detail
  endpoints.
Scaling path:
1. Fix inefficient queries, N+1 behavior, and oversized payloads.
2. Add justified indexes and bounded pagination.
3. Cache published content with locale-aware invalidation.
4. Scale stateless frontend/API instances horizontally.
5. Move slow side effects to bounded background workers.
6. Tune DB pools and query plans; scale PostgreSQL resources when
   measured.
7. Add replicas, partitioning, or separate analytics infrastructure
   only when justified.
8. Extract services only when benefits outweigh distributed-system
   complexity.
11. Testing and Verification
Required coverage should grow with the implementation:
- Unit tests for business rules, locale validation, fallback, and
  state transitions.
- Frontend tests for message loading, routing, language switching,
  lang/dir, and RTL-sensitive components.
- API tests for validation, error contracts, authorization, and locale
  behavior.
- DB integration tests for migrations, constraints, translation
  lookup, and bounded query behavior.
- Tenant-isolation tests for translated content and related resources.
- End-to-end tests for a critical localized event journey.
- Load tests for localized pages, registration, and check-in when
  implemented.
- Security tests for authorization bypass, cross-tenant access,
  webhook validation, and uploads as applicable.
Before a phase is marked complete:
- Relevant tests pass.
- Formatting, lint, type checks, and production build pass.
- Migrations work on a clean disposable test DB and safely against the
  intended development DB.
- No unexplained migration heads or schema drift.
- Critical queries are bounded and free of known N+1 behavior.
- Tenant isolation and authorization tests pass.
- English and Arabic paths are tested where relevant.
- Actual manual verification and limitations are recorded.
- Never claim a check passed unless it was executed and observed.
- Never reset/drop a database to bypass a migration problem.
12. Implementation Roadmap
Inspect the actual repository first. Do not assume the phases below are
unstarted or complete.
Phase 0 --- Foundation
- Inspect repository, runtime, package manager, dependencies, and
  environment.
- Establish configuration, logging, health/readiness, tests, linting,
  formatting, and type checks.
- Verify API startup/database readiness and verify frontend production
  build/live smoke test separately.
- Record approved architecture decisions in this document.
Phase 1 --- i18n foundation
- Verify installed Next.js and next-intl versions and compatible
  APIs.
- Implement en/ar locale routing.
- Add static message files and typed translation usage.
- Add accessible language switching and correct lang/dir.
- Preserve existing public/authenticated routes and API endpoints.
- Test valid/invalid locales and English/Arabic rendering.
Phase 2 --- RTL and localized UI
- Audit navigation, shared layouts, forms, tables, dialogs,
  pagination, and responsive behavior.
- Use logical CSS properties where appropriate.
- Localize dates, numbers, validation, loading, empty, and error
  states.
- Add frontend regression tests.
Phase 3 --- Dynamic translation model
- Inspect existing event models and migrations.
- Define translation entities, default locale, publication, fallback,
  uniqueness, and indexes.
- Implement only approved migrations and models.
- Test constraints without resetting or dropping existing data.
Phase 4 --- Localized API and public pages
- Define locale resolution for API requests.
- Fetch requested translations and bounded fallback.
- Implement localized event list/detail pages and metadata.
- Verify query count, indexing, caching, and tenant isolation.
Phase 5 --- Organizer translation workflow
- Let authorized organizers edit localized content.
- Add translation completeness and draft/publish behavior if required.
- Validate permissions and invalidate relevant caches after
  publishing.
Phase 6 --- Core event management
- Implement event lifecycle, registration, attendee management,
  capacity, and confirmations as approved.
- Protect retry-prone operations and concurrency.
Phase 7 --- Tickets, check-in, agenda, and communications
- Implement ticket/QR lifecycle, idempotent check-in, agenda, and
  asynchronous notifications as separately verifiable deliverables.
Phase 8 --- Analytics and reporting
- Use bounded dashboard queries, appropriate summaries, asynchronous
  exports, and explicit freshness guarantees.
Phase 9 --- Production hardening
- Load/security testing, profiling, observability, backup/restore
  drill, deployment runbooks, and measured capacity validation.
Do not start a later phase unless the owner requests it or approves a
revised plan.
13. Definition of Done
A feature is done only when applicable items are true:
- Behavior and edge cases are documented.
- Backend validation, authorization, and tenant scope are implemented.
- Locale routing/fallback is documented and tested where relevant.
- DB changes use migrations and preserve existing data.
- Queries are bounded, appropriately indexed, and free of known N+1
  behavior.
- Retry-sensitive writes are idempotent or otherwise protected.
- Slow side effects are asynchronous where appropriate.
- Loading, empty, error, and success states are handled.
- Tests include negative and permission cases.
- Lint, formatting, type checks, and production build pass.
- Logs/metrics aid diagnosis without leaking sensitive data.
- Actual verification results and known limitations are documented.
- No unrelated project files/specifications are modified.
14. AI Coding Assistant Instructions
Any AI coding assistant working in this repository must:
1. Read this complete PROJECT_SPEC.md before planning or editing.
2. Inspect actual files, dependencies, tests, and migrations before
   assuming repository state.
3. Treat this document as the source of truth. If code and spec
   conflict, report the conflict and propose the smallest safe
   resolution.
4. Never mix this repository with another project's requirements,
   architecture, or history.
5. Work in small, explicitly scoped phases with acceptance criteria and
   verification commands.
6. Preserve user changes and inspect files before overwriting.
7. Never reset/drop the development or production database or delete
   user data as a shortcut.
8. Never claim a command, test, build, endpoint, or UI flow passed
   unless it was actually run.
9. Prefer minimal, readable, typed, reusable code; avoid needless
   abstractions and dependencies.
10. Consider query count, indexes, tenant isolation, caching,
    idempotency, concurrency, and observability.
11. Use static i18n files for UI messages and database translations for
    organizer-created content.
12. Do not implement a language switcher without route preservation and
    missing-translation behavior.
13. Test both LTR and RTL; Arabic support is not translation-only.
14. Update this document only for meaningful, approved
    product/architecture changes and record them in the change log.
15. Do not commit or push unless explicitly asked.
16. Do not begin later roadmap phases merely because they are listed.
17. Use synthetic test data; never mutate real data without explicit
    approval.
18. Before finishing a phase, report summary, changed files, migration
    impact, actual tests/results, limitations, and recommended next
    phase.
Every phase prompt should define: goal, scope, out-of-scope items,
verified repository facts, expected behavior, affected modules,
migration impact, i18n/RTL impact, security/tenant impact,
performance/query considerations, acceptance tests, verification
commands, and explicit prohibitions.
15. Decisions Requiring Owner Approval
Do not silently invent choices affecting cost, security, architecture,
or user-visible behavior. Propose a default and ask when necessary:
- Product name, domain, audience, and launch market.
- Additional locales beyond initial en and ar.
- Default locale and locale-detection policy.
- Shared versus locale-specific event slugs.
- Translation draft/publish and approval workflow.
- Missing-content fallback for specific page types.
- Authentication/session provider and enterprise SSO.
- Payment provider, currencies, tax, refunds, and invoices.
- Email/SMS providers and consent requirements.
- Peak attendance, registrations, check-ins, concurrency, and
  availability goals.
- Data residency, retention, deletion, and privacy jurisdiction.
- Offline check-in, virtual-event provider, and mobile app
  requirements.
- Any new infrastructure service or destructive migration.
Use the simplest reversible option when safe, and document assumptions.
16. Change Log
- 2026-10-22: Regenerated the project source-of-truth
  specification. Established next-intl as the recommended frontend
  i18n approach; separated static UI messages from database-backed
  event content; defined en/ar routing, RTL, fallback, database
  performance, security, testing, and phased delivery. Existing
  implementation must be inspected before changes are applied.
Final Rule
Build a scalable, secure, maintainable event-management platform with
internationalization designed into its foundation. Keep locale
routing, static UI messages, database-backed content translations, and
RTL behavior distinct but coordinated. Protect PostgreSQL through
bounded and measured queries, short transactions, appropriate indexes,
and justified caching. Implement incrementally, preserve existing data,
and verify every claim with actual tes