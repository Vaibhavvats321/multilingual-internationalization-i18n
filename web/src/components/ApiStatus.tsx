'use client';

import {useTranslations} from 'next-intl';
import {useEffect, useState} from 'react';

import {StatusBadge, type StatusTone} from '@/components/StatusBadge';
import {fetchWebReadiness, type WebReadiness} from '@/lib/api/health';

type LoadState = 'loading' | 'ready' | 'failed';

export interface ApiStatusProps {
  readonly label: string;
}

/**
 * Live status of the API, rendered in the browser.
 *
 * The status is fetched from the web readiness proxy rather than from the
 * API directly, so the browser never needs to know the API origin and the
 * shell page itself stays statically renderable.
 */
export function ApiStatus({label}: ApiStatusProps) {
  const t = useTranslations('common');
  const [readiness, setReadiness] = useState<WebReadiness | null>(null);
  const [state, setState] = useState<LoadState>('loading');

  useEffect(() => {
    const controller = new AbortController();

    void fetchWebReadiness(controller.signal).then((result) => {
      if (controller.signal.aborted) {
        return;
      }
      setReadiness(result);
      setState(result === null ? 'failed' : 'ready');
    });

    return () => controller.abort();
  }, []);

  const apiStatus = readiness?.api?.status ?? null;

  const tone: StatusTone =
    state === 'loading'
      ? 'degraded'
      : state === 'failed'
        ? 'unavailable'
        : apiStatus === 'ok'
          ? 'ok'
          : 'degraded';
  const statusLabel =
    state === 'loading'
      ? t('statusChecking')
      : state === 'failed'
        ? t('statusUnavailable')
        : apiStatus === 'ok'
          ? t('statusOk')
          : t('statusDegraded');

  return (
    <li className="flex items-center justify-between gap-4">
      <span>{label}</span>
      <StatusBadge tone={tone} label={statusLabel} />
    </li>
  );
}
