import {getTranslations, setRequestLocale} from 'next-intl/server';
import {notFound} from 'next/navigation';

import {ApiStatus} from '@/components/ApiStatus';
import {StatusBadge} from '@/components/StatusBadge';
import {getDirection, isLocaleCode, localeCatalog} from '@/i18n/locales';

export interface HomePageProps {
  readonly params: Promise<{locale: string}>;
}

/**
 * Landing page of the platform shell.
 *
 * Phase 0 only proves that locale routing, the message catalogs and the API
 * health contract work end to end. The organizer dashboard and the public
 * event renderer arrive in later phases.
 */
export default async function HomePage({params}: HomePageProps) {
  const {locale} = await params;

  if (!isLocaleCode(locale)) {
    notFound();
  }

  setRequestLocale(locale);

  const t = await getTranslations('home');
  const tCommon = await getTranslations('common');

  return (
    <main className="mx-auto flex min-h-screen max-w-3xl flex-col gap-8 p-6">
      <header className="flex flex-col gap-2">
        <h1 className="text-3xl font-semibold">{t('title')}</h1>
        <p className="text-base text-neutral-600">{t('description')}</p>
      </header>

      <section
        aria-labelledby="status-heading"
        className="flex flex-col gap-3 rounded-lg border border-neutral-200 p-4"
      >
        <h2 id="status-heading" className="text-lg font-medium">
          {t('statusHeading')}
        </h2>

        <ul className="flex flex-col gap-2">
          <li className="flex items-center justify-between gap-4">
            <span>{tCommon('web')}</span>
            <StatusBadge tone="ok" label={tCommon('statusOk')} />
          </li>
          <ApiStatus label={tCommon('api')} />
        </ul>
      </section>

      <footer className="mt-auto text-sm text-neutral-500">
        <p>
          {t('localeLabel')}:{' '}
          <span dir={getDirection(locale)}>{localeCatalog[locale].nativeName}</span>
        </p>
        <p>
          {t('directionLabel')}: <code>{getDirection(locale)}</code>
        </p>
      </footer>
    </main>
  );
}
