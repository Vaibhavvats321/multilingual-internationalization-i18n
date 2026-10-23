# ADR 0003 — Locale routing strategy

- **Status:** Accepted
- **Date:** 2026-10-21
- **Scope:** Public URL structure, locale prefix, canonical and alternate links

## Context

Every event is published in several locales. The URL structure decides how
locales are discovered by search engines, how a visitor switches language
without losing the page, and how the application resolves the locale for
fixed UI strings, direction, formatting and content selection.

Spec §4.6 requires one consistent strategy, canonical and alternate-language
metadata, and locale switching that preserves the equivalent page.

## Decision

**Locale-prefixed paths: `/{locale}/events/{slug}`.**

1. The locale prefix is **always** present. `localePrefix: 'always'` is
   configured in `web/src/i18n/routing.ts`.
2. The locale segment is the first path segment for all user-facing routes:
   - `/{locale}` — platform shell (Phase 0)
   - `/{locale}/events/{slug}` — published event website
   - `/{locale}/events/{slug}/register` — registration flow
3. The root path `/` redirects to the visitor's best matching locale
   (Accept-Language, then the event's default locale, then `en`).
4. A request for a locale that is not in the supported catalog returns 404.
   A locale that is supported but not enabled for the requested event also
   returns 404 — it never falls back silently to another language.
5. The middleware/proxy is implemented with **next-intl** and lives in
   `web/src/proxy.ts` (Next.js 16 renamed the `middleware` file convention
   to `proxy`; the middleware signature is unchanged).
6. **Canonical and alternate links:** each published event page renders
   `alternates.languages` for every published locale plus a `canonical` URL
   pointing at the requested locale. The slug is language-independent, so
   switching locales keeps the same slug.
7. **Locale switching preserves the page.** The switcher links to the same
   route in the target locale. If the target locale is not published for the
   event, the switcher falls back to the event's default locale.
8. **Direction and formatting** come from the central locale catalog
   (`web/src/i18n/locales.ts`): the `dir` attribute on `<html>`, and
   `Intl`-based date/number formatting. CSS uses logical properties
   (`margin-inline-start`, `padding-inline-end`, `text-align: start`) so a
   single stylesheet serves both writing directions. URLs, e-mail addresses,
   phone numbers and numbers are never visually reversed in RTL.
9. Enabling a new locale on an existing event must not change the event ID,
   the slug or existing registrations (spec §4.2).

## Alternatives considered

| Alternative | Why it was rejected |
| --- | --- |
| `/events/{slug}/{locale}` | The locale is a secondary detail of a resource. This layout hides the language in the middle of the path, complicates the root redirect and makes language-only sites (`/en`, `/ar`) impossible to express cleanly. |
| `/events/{slug}` with a cookie/header-selected locale | The URL does not identify the language, so sharing and indexing break, and the "one site per language" requirement of the brief cannot be met. |
| `/events/{slug}?lang=ar` | Query-string locales are not crawlable per language and are easily lost in sharing. |
| Locale as a subdomain (`ar.example.com`) | Requires certificate and cookie-domain work for every locale, complicates local development and multi-tenant hosting. |
| No prefix at all, one site per event | The product explicitly asks for one application serving many event websites, in several languages, from a single codebase. |

## Consequences

- Every public route needs a locale segment, including error pages and
  static assets referenced from templates. The route matcher excludes
  `/api`, `/_next`, `/_vercel` and paths with a file extension.
- The locale segment is part of the cache key. Caches must be keyed by
  locale, and drafts must never share a cache entry with published content.
- Adding a locale requires no schema change: it is a catalog entry plus a
  per-event enablement row.
- The root redirect must be cached carefully; it varies by `Accept-Language`.

## Implementation status

Phase 0: the routing configuration, the middleware/proxy, the locale
catalog, the message catalogs and the locale-prefixed shell page exist and
are covered by tests. The public event renderer is Phase 2.
