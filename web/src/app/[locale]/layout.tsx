import type {Metadata} from 'next';
import {hasLocale, NextIntlClientProvider} from 'next-intl';
import {getMessages, setRequestLocale} from 'next-intl/server';
import {notFound} from 'next/navigation';
import type {ReactNode} from 'react';

import {getDirection} from '@/i18n/locales';
import {routing} from '@/i18n/routing';

import '../globals.css';

export const metadata: Metadata = {
  title: {
    default: 'Multilingual Event Platform',
    template: '%s | Multilingual Event Platform'
  },
  description: 'Create, publish and translate event websites.'
};

export function generateStaticParams() {
  return routing.locales.map((locale) => ({locale}));
}

export interface LocaleLayoutProps {
  readonly children: ReactNode;
  readonly params: Promise<{locale: string}>;
}

/**
 * Root layout.
 *
 * It lives inside the `[locale]` segment so that the document language and
 * the writing direction are always derived from the requested locale. There
 * is deliberately no `app/layout.tsx`: Next.js then treats this file as the
 * single root layout of the application.
 */
export default async function LocaleLayout({children, params}: LocaleLayoutProps) {
  const {locale} = await params;

  if (!hasLocale(routing.locales, locale)) {
    notFound();
  }

  setRequestLocale(locale);

  return (
    <html lang={locale} dir={getDirection(locale)}>
      <body>
        <NextIntlClientProvider messages={await getMessages()}>{children}</NextIntlClientProvider>
      </body>
    </html>
  );
}
