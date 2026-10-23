# ADR 0001 — Authentication and session handling

- **Status:** Accepted
- **Date:** 2026-10-21
- **Scope:** Organizer accounts, session cookies, CSRF protection

## Context

Organizers need accounts to create and publish events. The public event
websites are anonymous and must stay reachable without authentication.
Phase 0 does not implement any of it, but the storage and protocol decisions
determine the data model and the API contract, so they are fixed now.

Requirements that shaped the decision:

- Sessions must be revocable server-side.
- Passwords must never be stored or transmitted in recoverable form.
- The browser must not be able to read the session credential from JavaScript.
- State-changing requests must not be forgeable from a third-party site.
- The platform must be usable from several origins during local development.

## Decision

**Opaque server-side sessions.**

1. The password is hashed with **Argon2id** (argon2-cffi, memory-hard
   parameters tuned per deployment). A separate `password_version` column
   allows re-hashing on login.
2. On sign-in the server generates 32 random bytes with `secrets.token_urlsafe`
   and stores **only the SHA-256 hash** of the token. The raw token is handed
   to the browser once and never persisted.
3. The token is transported in an `HttpOnly`, `Secure` (in production),
   `SameSite=Lax` cookie named `session`. The `Path` attribute is `/`.
4. The `sessions` table stores `user_id`, `token_hash`, `created_at`,
   `expires_at`, `last_seen_at`, `ip_hash` and `user_agent_hash`. Rows are
   removed by a periodic cleanup job; expired tokens are rejected on every
   request regardless of cleanup state.
5. **CSRF protection uses the double-submit pattern**: a non-HttpOnly
   `csrf` cookie holds a random value that is also sent in the
   `X-CSRF-Token` request header. The server compares the header with the
   cookie using a constant-time comparison. State-changing methods
   (`POST`, `PUT`, `PATCH`, `DELETE`) are rejected with `403` when the header
   is missing or does not match. Cookies are additionally marked `SameSite`,
   so CSRF protection is defence in depth, not the only barrier.
6. Authorization is enforced **on the server for every request**. The client
   never decides whether a user may see or change an event; it only hides UI.
7. Endpoints are namespaced under `/api/v1`. The public renderer never
   receives session data it does not need, and draft content is never
   returned by a public endpoint.

## Alternatives considered

| Alternative | Why it was rejected |
| --- | --- |
| JWT access + refresh token | Refresh tokens are still stateful, and revocation requires a denylist — the same bookkeeping as a session table, with more cryptographic surface. |
| Server-rendered form sessions with a signed cookie (no DB) | Cannot be revoked before expiry; logout could not invalidate a stolen cookie. |
| Third-party identity provider (OIDC) | Adds an external dependency, an outage mode and a signup flow that the product does not need yet. Can be added later behind the same session interface. |
| HTTP Basic auth | Unsuitable for browsers and for the organizer dashboard. |
| Per-request signed CSRF tokens (stateless) | Compatible with the double-submit pattern, but requires serialising state into the token; the double-submit token is simpler and equally effective here. |

## Consequences

- Every authenticated request costs one indexed lookup on the `sessions`
  table. The index is on `token_hash`; this is acceptable at the expected
  scale and is measured before caching is considered.
- The session table is a sensitive store: it must be covered by the same
  access control and backup policy as user data.
- Argon2id is intentionally slow. Sign-in is protected by a rate limiter
  that is introduced with the auth module (Phase 1).
- Logging must never record raw tokens. Only the hash prefix may be logged
  for correlation, and the `redact()` helper in `api/app/core/logging.py`
  covers this.

## Implementation status

Phase 0: not implemented. The decision is recorded so that Phase 1 can
implement it without revisiting the storage shape.
