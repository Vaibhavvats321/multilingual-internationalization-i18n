import {createNavigation} from 'next-intl/navigation';

import {routing} from './routing';

/**
 * Locale aware navigation helpers. `Link` keeps the active locale in the
 * URL, and `usePathname`/`useRouter` operate on the locale-less path.
 */
export const {Link, redirect, usePathname, useRouter, getPathname} = createNavigation(routing);
