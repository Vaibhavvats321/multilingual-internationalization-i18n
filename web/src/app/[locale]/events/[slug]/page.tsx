import {getTranslations, setRequestLocale} from 'next-intl/server';

export interface EventPageProps {
  readonly params: Promise<{locale: string; slug: string}>;
}

/**
 * Placeholder for the public event website.
 *
 * Phase 2 replaces this with the published event renderer. The route exists
 * now so that the locale prefixed URL strategy
 * (`/{locale}/events/{slug}`, see docs/decisions/0003-locale-routing.md) is
 * exercised end to end from the first release.
 */
export default async function EventPage({params}: EventPageProps) {
  const {locale, slug} = await params;
  setRequestLocale(locale);

  const t = await getTranslations('event');

  return (
    <main className="mx-auto flex min-h-screen max-w-3xl flex-col gap-4 p-6">
      <h1 className="text-3xl font-semibold">{slug}</h1>
      <p className="text-base text-neutral-600">{t('placeholder')}</p>
    </main>
  );
}
