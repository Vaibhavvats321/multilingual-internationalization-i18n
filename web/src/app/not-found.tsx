import {getTranslations} from 'next-intl/server';

export default async function NotFound() {
  const t = await getTranslations({locale: 'en', namespace: 'common'});

  return (
    <main
      lang="en"
      dir="ltr"
      className="mx-auto flex min-h-screen max-w-3xl flex-col gap-4 p-6"
    >
      <h1 className="text-3xl font-semibold">{t('notFoundTitle')}</h1>
      <p className="text-base text-neutral-600">{t('notFoundDescription')}</p>
    </main>
  );
}
