import {describe, expect, it} from 'vitest';

import {
  getDirection,
  getLocaleDefinition,
  isLocaleCode,
  localeCatalog,
  localeCodes
} from '../src/i18n/locales';

describe('supported locale catalog', () => {
  it('lists every catalog entry in the locale code list', () => {
    expect(Object.keys(localeCatalog).sort()).toEqual([...localeCodes].sort());
  });

  it('stores the locale code as the catalog key', () => {
    for (const code of localeCodes) {
      expect(localeCatalog[code].code).toBe(code);
    }
  });

  it('marks Arabic as right-to-left and the others as left-to-right', () => {
    expect(getDirection('ar')).toBe('rtl');
    expect(getDirection('en')).toBe('ltr');
    expect(getDirection('de')).toBe('ltr');
  });

  it('recognises supported locales only', () => {
    expect(isLocaleCode('en')).toBe(true);
    expect(isLocaleCode('ar')).toBe(true);
    expect(isLocaleCode('de')).toBe(true);
    expect(isLocaleCode('fr')).toBe(false);
    expect(isLocaleCode('')).toBe(false);
  });

  it('exposes a native and an english name for every locale', () => {
    for (const code of localeCodes) {
      const definition = getLocaleDefinition(code);
      expect(definition.englishName.length).toBeGreaterThan(0);
      expect(definition.nativeName.length).toBeGreaterThan(0);
    }
  });
});
