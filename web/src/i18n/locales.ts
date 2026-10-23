/**
 * Central supported-locale catalog.
 *
 * This is the single source of truth for the locales the platform can render.
 * Adding a language must never require a database migration, so the catalog
 * lives in code and is referenced by the router, the direction helpers and
 * the admin UI.
 *
 * See PROJECT_SPEC.md section 4.2.
 */

export const localeCodes = ['en', 'ar', 'de'] as const;

export type LocaleCode = (typeof localeCodes)[number];

export type Direction = 'ltr' | 'rtl';

export interface LocaleDefinition {
  /** BCP 47 language identifier. */
  readonly code: LocaleCode;
  /** English name, used for logs and administrative listings. */
  readonly englishName: string;
  /** Name in the language itself, used in the language selector. */
  readonly nativeName: string;
  /** Base writing direction. */
  readonly direction: Direction;
}

export const localeCatalog: Readonly<Record<LocaleCode, LocaleDefinition>> = {
  en: {code: 'en', englishName: 'English', nativeName: 'English', direction: 'ltr'},
  ar: {code: 'ar', englishName: 'Arabic', nativeName: 'العربية', direction: 'rtl'},
  de: {code: 'de', englishName: 'German', nativeName: 'Deutsch', direction: 'ltr'}
};

export function isLocaleCode(value: string): value is LocaleCode {
  return (localeCodes as readonly string[]).includes(value);
}

export function getDirection(locale: LocaleCode): Direction {
  return localeCatalog[locale].direction;
}

export function getLocaleDefinition(locale: LocaleCode): LocaleDefinition {
  return localeCatalog[locale];
}
