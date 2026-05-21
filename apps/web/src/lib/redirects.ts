// Redirect helpers for auth flows. Keep callback handling centralized so every
// sign-in path applies the same same-origin and locale checks.
import { hasLocale } from "next-intl";

import { localizedPath } from "@/i18n/paths";
import { routing } from "@/i18n/routing";

export function safeLocalizedCallbackUrl(
  value: string | string[] | undefined,
  locale: string,
): `/${string}` {
  const fallback = localizedPath("/", locale);
  const safeLocale = hasLocale(routing.locales, locale)
    ? locale
    : routing.defaultLocale;
  const rawValue = Array.isArray(value) ? value[0] : value;

  if (
    !rawValue ||
    !rawValue.startsWith("/") ||
    rawValue.startsWith("//") ||
    rawValue.includes("\\") ||
    rawValue.includes("\n") ||
    rawValue.includes("\r")
  ) {
    return fallback;
  }

  try {
    const parsedUrl = new URL(rawValue, "http://localhost");
    const localePrefix = `/${safeLocale}`;
    if (
      parsedUrl.origin === "http://localhost" &&
      (parsedUrl.pathname === localePrefix ||
        parsedUrl.pathname.startsWith(`${localePrefix}/`))
    ) {
      return `${parsedUrl.pathname}${parsedUrl.search}${parsedUrl.hash}` as `/${string}`;
    }
  } catch {
    return fallback;
  }

  return fallback;
}
