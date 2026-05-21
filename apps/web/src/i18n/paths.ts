// Shared locale path helpers for APIs that need plain redirect strings.
import { routing } from "./routing";

export type AppRoute =
  | "/"
  | "/login"
  | "/profile"
  | "/challenges/coding"
  | "/board"
  | "/billing";

export function localizedPath(
  path: AppRoute,
  locale: string = routing.defaultLocale,
): `/${string}` {
  const suffix = path === "/" ? "" : path;
  return `/${locale}${suffix}`;
}

export function defaultLocalePath(path: AppRoute): `/${string}` {
  return localizedPath(path, routing.defaultLocale);
}
