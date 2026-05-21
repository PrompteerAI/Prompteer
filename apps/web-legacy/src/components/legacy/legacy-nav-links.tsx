// Client-side active-link navigation for the legacy-preview header.
"use client";

import { useTranslations } from "next-intl";

import { Link, usePathname } from "@/i18n/navigation";

const navItems = [
  { href: "/board", labelKey: "board" },
  { href: "/category/coding", labelKey: "algorithm" },
  { href: "/category/image", labelKey: "image" },
  { href: "/category/video", labelKey: "video" },
] as const;

export function LegacyNavLinks(): React.ReactElement {
  const t = useTranslations("legacy.nav");
  const pathname = usePathname();

  return (
    <div className="legacy-nav">
      {navItems.map((item) => {
        const isActive = isLegacyNavActive(pathname, item.href);
        return (
          <Link
            aria-current={isActive ? "page" : undefined}
            className={isActive ? "active" : undefined}
            href={item.href}
            key={item.href}
          >
            {t(item.labelKey)}
          </Link>
        );
      })}
    </div>
  );
}

function isLegacyNavActive(
  pathname: string,
  href: (typeof navItems)[number]["href"],
): boolean {
  const routePath = stripLocalePrefix(pathname);
  if (routePath === href || routePath.startsWith(`${href}/`)) {
    return true;
  }

  if (href === "/board") {
    return (
      routePath.startsWith("/board/post/") ||
      routePath.startsWith("/board/shared/")
    );
  }
  if (href === "/category/coding") {
    return routePath.startsWith("/coding/problem/");
  }
  if (href === "/category/image") {
    return routePath.startsWith("/image/challenge/");
  }
  if (href === "/category/video") {
    return routePath.startsWith("/video/challenge/");
  }
  return false;
}

function stripLocalePrefix(pathname: string): string {
  const localePrefix = pathname.match(/^\/[a-z]{2}(?=\/|$)/);
  if (!localePrefix) {
    return pathname;
  }
  return pathname.slice(localePrefix[0].length) || "/";
}
