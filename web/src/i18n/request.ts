import {hasLocale} from 'next-intl';
import {getRequestConfig} from 'next-intl/server';

import {routing} from './routing';

/**
 * Static imports keep the message catalogs typed and let the bundler include
 * exactly the three files. A new language is added by extending this map and
 * the locale catalog - no other wiring changes.
 */
const messageCatalogs = {
  en: () => import('../../messages/en.json'),
  ar: () => import('../../messages/ar.json'),
  de: () => import('../../messages/de.json')
} as const;

export default getRequestConfig(async ({requestLocale}) => {
  const requested = await requestLocale;
  const locale = hasLocale(routing.locales, requested) ? requested : routing.defaultLocale;

  return {
    locale,
    messages: (await messageCatalogs[locale]()).default
  };
});
