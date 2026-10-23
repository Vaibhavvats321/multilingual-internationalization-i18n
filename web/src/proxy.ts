import {hasLocale} from 'next-intl';
import createMiddleware from 'next-intl/middleware';
import {NextResponse, type NextRequest} from 'next/server';

import {routing} from './i18n/routing';

const handleI18nRouting = createMiddleware(routing);

function isLocaleLike(segment: string) {
  return /^[a-z]{2}(?:-[a-z]{2,})?$/i.test(segment);
}

/**
 * Locale routing proxy.
 *
 * Next.js 16 replaced the `middleware` file convention with `proxy`; the
 * signature is unchanged, so next-intl's middleware factory is reused as is.
 */
export default function proxy(request: NextRequest) {
  const segment = request.nextUrl.pathname.split('/')[1];

  if (segment && isLocaleLike(segment) && !hasLocale(routing.locales, segment)) {
    const url = request.nextUrl.clone();
    url.pathname = `/${routing.defaultLocale}${request.nextUrl.pathname}`;
    return NextResponse.rewrite(url);
  }

  return handleI18nRouting(request);
}

export const config = {
  // Skip API routes, Next.js internals and any path containing a file
  // extension (static assets).
  matcher: ['/((?!api|_next|_vercel|.*\\..*).*)']
};
