import {NextResponse} from 'next/server';

import {fetchReadiness, getApiReadinessUrl} from '@/lib/api/health';

/**
 * Readiness probe for the web process.
 *
 * The web tier cannot render public event pages without the API, so the
 * probe reports `503` when the API is unreachable. The web process itself
 * stays alive and is restarted only by the liveness probe.
 */
export const dynamic = 'force-dynamic';

export async function GET() {
  const api = await fetchReadiness(getApiReadinessUrl());
  const ready = api !== null && api.status === 'ok';

  return NextResponse.json(
    {
      status: ready ? 'ok' : 'unavailable',
      service: 'multilingua-web',
      api
    },
    {status: ready ? 200 : 503}
  );
}
