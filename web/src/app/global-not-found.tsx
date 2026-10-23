import {getLocale, getTranslations} from 'next-intl/server';

import {getDirection, isLocaleCode} from '@/i18n/locales';

import './globals.css';

export default async function GlobalNotFound() {
  const requested = await getLocale();
  const locale = isLocaleCode(requested) ? requested : 'en';
  const t = await getTranslations({locale, namespace: 'common'});

  return (
    <html lang={locale} dir={getDirection(locale)}>
      <body>
        <main className="mx-auto flex min-h-screen max-w-3xl flex-col gap-4 p-6">
          <h1 className="text-3xl font-semibold">{t('notFoundTitle')}</h1>
          <p className="text-base text-neutral-600">{t('notFoundDescription')}</p>
        </main>
      </body>
    </html>
  );
}
