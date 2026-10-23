import {describe, expect, it} from 'vitest';

import {readinessSchema} from '../src/lib/api/health';

describe('API readiness schema', () => {
  it('accepts a healthy readiness report', () => {
    const parsed = readinessSchema.parse({
      status: 'ok',
      service: 'multilingua-api',
      version: '0.1.0',
      checks: [{name: 'database', status: 'ok', detail: null}]
    });

    expect(parsed.status).toBe('ok');
    expect(parsed.checks).toHaveLength(1);
  });

  it('accepts a report without checks', () => {
    const parsed = readinessSchema.parse({
      status: 'ok',
      service: 'multilingua-api',
      version: '0.1.0'
    });

    expect(parsed.checks).toEqual([]);
  });

  it('rejects an unknown status', () => {
    const result = readinessSchema.safeParse({
      status: 'broken',
      service: 'multilingua-api',
      version: '0.1.0'
    });

    expect(result.success).toBe(false);
  });

  it('rejects a payload that is missing the service name', () => {
    const result = readinessSchema.safeParse({
      status: 'ok',
      version: '0.1.0'
    });

    expect(result.success).toBe(false);
  });
});
