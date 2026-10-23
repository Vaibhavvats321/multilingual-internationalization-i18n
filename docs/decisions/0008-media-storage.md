# ADR 0008 — Media storage

- **Status:** Accepted
- **Date:** 2026-10-21
- **Scope:** Images, logos, attachments, downloads

## Context

Event websites need images: logos, hero images, speaker photos, and
downloadable documents (agendas, vouchers, brochures). The platform must
decide where these bytes live, how they are served, and how the public site
references them.

Phase 0 does not implement uploads, but the decision affects the schema
(media records), the configuration and the deployment story, so it is
recorded now. Spec §10 defers media storage to Phase 7.

## Decision

**Object storage behind a storage adapter, with a local filesystem driver as
the default. The database stores metadata only.**

1. **Bytes never go into PostgreSQL.** Only metadata is stored: media id,
   owner, event, original filename, MIME type, byte size, checksum, storage
   key, created timestamp, processing state.
2. **A `MediaStorage` adapter interface** defines the operations the
   application needs — `put`, `get`, `delete`, `presign`. The domain code
   depends on the interface, not on a vendor SDK.
3. **Two drivers are planned:**
   - **Local filesystem** — the default in development. Files are written
     under a configurable root, and the web application serves them through
     a controlled route that checks authorisation.
   - **S3-compatible object storage** — the target in production. The
     adapter uses presigned URLs so that the browser downloads directly
     and the application server does not proxy large files.
4. **`OBJECT_STORAGE_*` configuration names exist in `.env.example` but are
   unset by default.** No provider is assumed to be configured, and the
   local driver works with zero configuration.
5. **Uploads are validated server-side** on MIME type, size and, for
   images, actual content (magic bytes). The declared content type is never
   trusted. A per-event quota and a per-user quota prevent abuse.
6. **Filenames are never trusted.** The stored key is generated from a
   random identifier plus a normalised extension; the original filename is
   kept as metadata for display only and is always escaped on output.
7. **Private media is never exposed through a public URL.** Public assets
   are copied to a public bucket or served by a route that checks the
   event's published state.
8. **Checksums are stored** so that duplicates can be detected and so that
   the integrity of an object can be verified after a restore.
9. **Deletion is a two-step operation**: the row is marked for deletion, the
   object is removed, and the row is purged. A failed object deletion is
   retried by the background worker (ADR 0006) and never leaves a dangling
   reference in a published page.
10. **Derivatives are generated in the background** (thumbnails, resized
    hero images) and never in the request path.

## Alternatives considered

| Alternative | Why it was rejected |
| --- | --- |
| Store the files in PostgreSQL as bytea | Bloats the database, mixes binary and relational backups, and serves large files from the application server. |
| Keep a single volume on the API host | Works for a first prototype, but makes the deployment non-reproducible and the backup story unclear. |
| Let the browser upload straight to the vendor SDK | Saves server bandwidth, but the application then cannot validate the content, enforce quotas or record the metadata transactionally. |
| Commit assets to Git | Only viable for a small set of shared, versioned assets — not for organizer uploads. |
| Pin a specific vendor SDK in the domain layer | Couples the code to one vendor; the adapter keeps the domain code portable. |

## Consequences

- A storage driver and an `OBJECT_STORAGE_*` configuration block are needed
  in Phase 7, together with an upload endpoint, validation and a cleanup
  job.
- Local development needs a writable media root; the path is configured and
  git-ignored.
- The public site references media through URLs that are stable across
  deployments, so that a switch from the local driver to object storage does
  not break published pages.
- Because the metadata is in the database and the bytes are not, a database
  restore alone does not restore the media. The backup runbook must cover
  the media store explicitly.

## Implementation status

Phase 0: configuration names and the ADR only. No upload code exists.
