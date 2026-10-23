import {defineRouting} from 'next-intl/routing';

import {localeCodes} from './locales';

/**
 * Public URL strategy.
 *
 * The locale is always the first path segment (`/{locale}/events/{slug}`),
 * so every public page has exactly one canonical URL and the alternate
 * language links are unambiguous. See docs/decisions/0003-locale-routing.md.
 */
export const routing = defineRouting({
  locales: localeCodes,
  defaultLocale: 'en',
  localePrefix: 'always'
});

export type Locale = (typeof routing.locales)[number];
