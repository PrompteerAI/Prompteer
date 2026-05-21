// Protected app route-group layout. Public marketing/login routes live outside
// this group; every product surface here requires an Auth.js session.
import { redirect } from "next/navigation";
import { getTranslations } from "next-intl/server";

import { Link } from "@/i18n/navigation";
import { localizedPath } from "@/i18n/paths";
import { auth } from "@/lib/auth";

type Props = {
  children: React.ReactNode;
  params: Promise<{ locale: string }>;
};

export default async function AppLayout({
  children,
  params,
}: Props): Promise<React.ReactElement> {
  const session = await auth();
  if (!session?.user) {
    const { locale } = await params;
    redirect(localizedPath("/login", locale));
  }
  const t = await getTranslations("nav");
  const navItems = [
    { href: "/" as const, label: t("home") },
    { href: "/challenges/coding" as const, label: t("challenges") },
    { href: "/board" as const, label: t("board") },
    { href: "/billing" as const, label: t("billing") },
    { href: "/profile" as const, label: t("profile") },
  ];

  return (
    <div className="min-h-screen bg-zinc-50 text-zinc-950">
      <header className="border-b border-zinc-200 bg-white">
        <nav
          aria-label={t("label")}
          className="mx-auto flex max-w-6xl flex-col gap-3 px-6 py-4 sm:flex-row sm:items-center sm:justify-between"
        >
          <Link
            className="inline-flex min-h-11 items-center text-base font-semibold text-zinc-950"
            href="/"
          >
            Prompteer
          </Link>
          <div className="flex flex-wrap gap-1 sm:flex-nowrap">
            {navItems.map((item) => (
              <Link
                className="inline-flex min-h-10 items-center rounded-md px-2.5 text-sm font-medium text-zinc-700 transition hover:bg-zinc-100 hover:text-zinc-950 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-zinc-950 sm:min-h-11 sm:px-3"
                href={item.href}
                key={item.href}
              >
                {item.label}
              </Link>
            ))}
          </div>
        </nav>
      </header>
      {children}
    </div>
  );
}
