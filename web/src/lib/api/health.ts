import {z} from 'zod';

/**
 * Typed client for the API and web health endpoints.
 *
 * The API is the system of record for everything the public site renders, so
 * the frontend validates the response shape at runtime instead of trusting
 * it. A response that does not match the schema is treated as "unavailable"
 * rather than as a partial success.
 */

export const dependencyStatusSchema = z.enum(['ok', 'degraded', 'unavailable', 'skipped']);

export const readinessSchema = z.object({
  status: dependencyStatusSchema,
  service: z.string(),
  version: z.string(),
  checks: z
    .array(
      z.object({
        name: z.string(),
        status: dependencyStatusSchema,
        detail: z.string().nullable().optional()
      })
    )
    .default([])
});

export type ApiReadiness = z.infer<typeof readinessSchema>;

export const webReadinessSchema = z.object({
  status: z.enum(['ok', 'unavailable']),
  service: z.string(),
  api: readinessSchema.nullable()
});

export type WebReadiness = z.infer<typeof webReadinessSchema>;

const DEFAULT_API_BASE_URL = 'http://localhost:8000';

/** Relative path of the web readiness proxy. Safe to call from the browser. */
export const WEB_READINESS_PATH = '/api/health/ready';

export function getApiBaseUrl(): string {
  return process.env.NEXT_PUBLIC_API_BASE_URL ?? DEFAULT_API_BASE_URL;
}

/** Absolute URL of the API readiness endpoint. Server side only. */
export function getApiReadinessUrl(): string {
  return new URL('/api/v1/health/ready', getApiBaseUrl()).toString();
}

/**
 * Fetch and validate a readiness report.
 *
 * Returns `null` when the endpoint cannot be reached or answers with an
 * unexpected payload. Callers must treat `null` as "not ready".
 */
export async function fetchReadiness(
  url: string,
  signal?: AbortSignal
): Promise<ApiReadiness | null> {
  try {
    const response = await fetch(url, {
      signal,
      cache: 'no-store',
      headers: {accept: 'application/json'}
    });

    if (!response.ok) {
      return null;
    }

    return readinessSchema.parse(await response.json());
  } catch (error) {
    console.error('[api] readiness request failed', {
      reason: error instanceof Error ? error.message : 'unknown error'
    });
    return null;
  }
}

/** Fetch the web readiness proxy from the browser. */
export async function fetchWebReadiness(signal?: AbortSignal): Promise<WebReadiness | null> {
  try {
    const response = await fetch(WEB_READINESS_PATH, {
      signal,
      cache: 'no-store',
      headers: {accept: 'application/json'}
    });

    if (!response.ok) {
      return null;
    }

    return webReadinessSchema.parse(await response.json());
  } catch (error) {
    console.error('[web] readiness request failed', {
      reason: error instanceof Error ? error.message : 'unknown error'
    });
    return null;
  }
}
