// Shared locale path helpers for APIs that need plain redirect strings.
import { hasLocale } from "next-intl";

import { defaultLocale, locales } from "./locales.generated";
import { routing } from "./routing";

export type AppRoute =
  | "/"
  | "/login"
  | "/profile"
  | "/challenges/coding"
  | "/challenges/image"
  | "/challenges/video"
  | "/board"
  | "/billing";

export function localizedPath(
  path: AppRoute,
  locale: string = routing.defaultLocale,
): `/${string}` {
  const safeLocale = hasLocale(locales, locale) ? locale : defaultLocale;
  const suffix = path === "/" ? "" : path;
  return `/${safeLocale}${suffix}`;
}

export function defaultLocalePath(path: AppRoute): `/${string}` {
  return localizedPath(path, routing.defaultLocale);
}
