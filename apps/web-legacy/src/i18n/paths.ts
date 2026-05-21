// Shared locale path helpers for redirects and plain anchors.
import { hasLocale } from "next-intl";

import { defaultLocale, locales } from "./locales.generated";
import { routing } from "./routing";

export function localizedPath(
  path: string,
  locale: string = routing.defaultLocale,
): `/${string}` {
  const safeLocale = hasLocale(locales, locale) ? locale : defaultLocale;
  const suffix = path === "/" ? "" : path.startsWith("/") ? path : `/${path}`;
  return `/${safeLocale}${suffix}`;
}

export function defaultLocalePath(path: string): `/${string}` {
  return localizedPath(path, routing.defaultLocale);
}
