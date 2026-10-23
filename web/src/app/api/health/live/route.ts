import {NextResponse} from 'next/server';

/**
 * Liveness probe for the web process.
 *
 * It deliberately does not touch the API: a backend outage must not cause an
 * orchestrator to restart healthy web processes.
 */
export const dynamic = 'force-dynamic';

export function GET() {
  return NextResponse.json({
    status: 'ok',
    service: 'multilingua-web'
  });
}
