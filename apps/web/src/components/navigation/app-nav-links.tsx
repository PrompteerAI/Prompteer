// Client-side active-link navigation for authenticated app routes.
"use client";

import { Link, usePathname } from "@/i18n/navigation";
import { locales } from "@/i18n/locales.generated";
import type { AppRoute } from "@/i18n/paths";

type NavItem = {
  href: AppRoute;
  label: string;
};

type AppNavLinksProps = {
  items: NavItem[];
};

export function AppNavLinks({ items }: AppNavLinksProps): React.ReactElement {
  const pathname = usePathname();

  return (
    <div className="-mx-1 flex max-w-full gap-1 overflow-x-auto pb-1 sm:mx-0 sm:overflow-visible sm:pb-0">
      {items.map((item) => {
        const visualCurrent = isCurrentPath(pathname, item.href);
        const pageCurrent = isExactPath(pathname, item.href);
        return (
          <Link
            aria-current={pageCurrent ? "page" : undefined}
            className={
              visualCurrent
                ? "inline-flex min-h-9 shrink-0 items-center rounded-md bg-zinc-950 px-2.5 text-sm font-medium text-white transition focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-zinc-950 sm:min-h-11 sm:px-3"
                : "inline-flex min-h-9 shrink-0 items-center rounded-md px-2.5 text-sm font-medium text-zinc-700 transition hover:bg-zinc-100 hover:text-zinc-950 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-zinc-950 sm:min-h-11 sm:px-3"
            }
            href={item.href}
            key={item.href}
          >
            {item.label}
          </Link>
        );
      })}
    </div>
  );
}

function isCurrentPath(pathname: string, href: AppRoute): boolean {
  const routePath = unlocalizedPath(pathname);
  if (href === "/") {
    return routePath === "/";
  }
  if (href === "/challenges/coding") {
    return routePath.startsWith("/challenges/");
  }
  return routePath === href || routePath.startsWith(`${href}/`);
}

function isExactPath(pathname: string, href: AppRoute): boolean {
  return unlocalizedPath(pathname) === href;
}

function unlocalizedPath(pathname: string): string {
  for (const locale of locales) {
    if (pathname === `/${locale}`) {
      return "/";
    }
    if (pathname.startsWith(`/${locale}/`)) {
      return pathname.slice(locale.length + 1);
    }
  }
  return pathname;
}
