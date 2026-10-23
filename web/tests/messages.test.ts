import {describe, expect, it} from 'vitest';

import ar from '../messages/ar.json';
import de from '../messages/de.json';
import en from '../messages/en.json';

type MessageValue = string | {[key: string]: MessageValue};

const catalogs = {
  en,
  ar,
  de
} as const;

function flattenKeys(value: MessageValue, prefix = ''): string[] {
  if (typeof value === 'string') {
    return [prefix];
  }

  return Object.entries(value).flatMap(([key, child]) =>
    flattenKeys(child, prefix ? `${prefix}.${key}` : key)
  );
}

function flattenEntries(
  value: MessageValue,
  prefix = ''
): Array<[string, string]> {
  if (typeof value === 'string') {
    return [[prefix, value]];
  }

  return Object.entries(value).flatMap(([key, child]) =>
    flattenEntries(child, prefix ? `${prefix}.${key}` : key)
  );
}

describe('fixed UI message catalogs', () => {
  const referenceKeys = flattenKeys(en).sort();

  it('exposes the same keys in every locale', () => {
    for (const [locale, catalog] of Object.entries(catalogs)) {
      expect(flattenKeys(catalog).sort(), `locale ${locale}`).toEqual(referenceKeys);
    }
  });

  it('has no empty messages', () => {
    for (const [locale, catalog] of Object.entries(catalogs)) {
      for (const [key, value] of flattenEntries(catalog)) {
        expect(value.trim(), `${locale}.${key}`).not.toBe('');
      }
    }
  });

  it('keeps ICU placeholders balanced', () => {
    for (const [locale, catalog] of Object.entries(catalogs)) {
      for (const [key, value] of flattenEntries(catalog)) {
        const open = (value.match(/\{/g) ?? []).length;
        const close = (value.match(/\}/g) ?? []).length;
        expect(open, `${locale}.${key}`).toBe(close);
      }
    }
  });

  it('declares at least one message', () => {
    expect(referenceKeys.length).toBeGreaterThan(0);
  });
});
