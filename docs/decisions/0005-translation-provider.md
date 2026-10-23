# ADR 0005 — Translation provider strategy

- **Status:** Accepted
- **Date:** 2026-10-21
- **Scope:** Provider abstraction, credentials, quality control, costs

## Context

Event content is translated automatically and then reviewed by an organizer
(spec §4.3, §4.4). Translation is an external, network-bound, rate-limited
operation that can be slow, expensive and wrong. The platform must work
when no provider is configured, must not expose provider credentials, and
must never let a provider failure damage the original content.

## Decision

**A provider adapter interface, with providers treated as optional and
machine output always remaining a draft.**

1. **One narrow interface** in the API, implemented per provider:
   ```python
   class TranslationProvider(Protocol):
       name: str
       async def translate_batch(self, units: list[TranslationUnit]) -> list[TranslationResult]: ...
   ```
   The domain logic depends only on this interface, so a provider can be
   swapped without touching event or translation code.
2. **Providers are pluggable and optional.** `TRANSLATION_PROVIDER` selects
   the adapter; when it is unset or the key is missing, the platform runs in
   **manual-only mode** and the UI offers manual translation. No provider is
   ever assumed to be configured.
3. **Credentials are server-side only.** `TRANSLATION_API_KEY` is read from
   the server environment. It is never exposed through a `NEXT_PUBLIC_*`
   variable, never returned by an API endpoint and never logged. The
   `redact()` helper in `api/app/core/logging.py` scrubs it from log output.
4. **Providers are never called on a public page request.** Translation runs
   only in a background job (ADR 0006).
5. **Every provider call has a timeout, bounded retries with exponential
   backoff and jitter, and a rate limit.** A call that exhausts its budget
   fails the job, it does not hang the worker.
6. **Idempotency:** a job is identified by
   `(event_id, locale, source_revision, scope)`. The unique index on
   `translation_jobs.idempotency_key` prevents duplicate jobs for the same
   input.
7. **Partial failure is a first-class state.** Each unit carries its own
   success/failure state; a failed unit is retried on its own and never
   overwrites a successful result.
8. **The source content is never overwritten.** Provider output is written
   as a new draft revision; the organizer's edits are preserved and a
   changed source marks previous translations `outdated` instead of
   deleting them.
9. **Quality control:** machine output is a draft and is never published
   automatically. The organizer's review is required, and review is
   mandatory for legal, safety, pricing, schedule and registration-policy
   text.
10. **Placeholders and structure are preserved.** The unit sent to a
    provider is a string with named placeholders (`{name}`), links and
    structured-content boundaries. The adapter verifies that the returned
    text contains the same placeholder set; a mismatch fails the unit
    instead of publishing broken text.
11. **Cost and privacy controls:** a per-event quota and a global daily
    budget are tracked in `translation_jobs`; exceeding them stops new jobs
    and surfaces the reason in the organizer UI. Only the text that needs
    translating is sent — never attendee data, never personal data.

## Alternatives considered

| Alternative | Why it was rejected |
| --- | --- |
| Calling a provider directly from the request handler | Blocks the request, hits provider rate limits under load and makes failures visible to public visitors. |
| One hard-coded provider | Any change of provider would touch domain code; the spec requires a swappable interface. |
| Publishing machine output automatically | Wrong translations are a real risk for dates, prices and policies. The spec forbids auto-publishing. |
| Sending whole pages to the provider | Breaks placeholder alignment, wastes tokens and makes per-field review impossible. |
| Self-hosting an open translation model | Significant operational cost and quality risk; it can be added later as another adapter behind the same interface. |
| Browser-side translation APIs | Leaks content to third parties and gives no control over credentials, retries or cost. |

## Consequences

- The provider interface is deliberately small; a new provider needs one
  adapter and one set of contract tests.
- Manual translation is a first-class path, not a fallback hack, so the
  platform is fully usable with no provider at all.
- The system must model per-unit and per-job failure states, which is more
  schema and more UI work than a boolean "translated" flag.
- The budget and quota machinery is a hard requirement for cost control and
  must be in place before the first production provider is enabled.
- Provider output quality varies; the review workflow is a product
  requirement, not an optional extra.

## Implementation status

Phase 0: the configuration names and the manual-only default are defined.
The adapter interface and the job implementation are Phase 5.
