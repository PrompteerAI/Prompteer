// Localized home workspace with entry points into the seeded demo flows.
import {
  ArrowRight,
  Code2,
  CreditCard,
  LogIn,
  LogOut,
  MessageSquareText,
} from "lucide-react";
import { getTranslations } from "next-intl/server";

import { auth, signOut } from "@/lib/auth";

const entrypoints = [
  { key: "login", icon: LogIn, href: "/en/login" },
  { key: "coding", icon: Code2, href: "/en/challenges/coding" },
  { key: "board", icon: MessageSquareText, href: "/en/board" },
  { key: "billing", icon: CreditCard, href: "/en/billing" },
] as const;

async function signOutAction(): Promise<void> {
  "use server";

  await signOut({ redirectTo: "/en/login" });
}

export default async function HomePage(): Promise<React.ReactElement> {
  const t = await getTranslations("home");
  const session = await auth();

  return (
    <main className="min-h-screen bg-zinc-50 text-zinc-950">
      <section className="mx-auto w-full max-w-6xl px-6 py-8">
        <div className="flex flex-col gap-6 md:flex-row md:items-start md:justify-between">
          <div className="max-w-3xl">
            <p className="text-sm font-semibold uppercase text-emerald-700">
              {t("brand")}
            </p>
            <h1 className="mt-4 text-5xl font-semibold leading-tight text-zinc-950">
              {t("title")}
            </h1>
            <p className="mt-5 max-w-2xl text-lg leading-8 text-zinc-600">
              {t("subtitle")}
            </p>
          </div>
          {session?.user ? (
            <form
              action={signOutAction}
              className="flex items-center gap-3 rounded-lg border border-zinc-200 bg-white p-3 shadow-sm"
            >
              <span className="max-w-48 truncate text-sm font-medium text-zinc-700">
                {session.user.name ?? session.user.email}
              </span>
              <button
                className="inline-flex h-9 items-center gap-2 rounded-md border border-zinc-300 px-3 text-sm font-medium text-zinc-900 transition hover:bg-zinc-50"
                type="submit"
              >
                <LogOut aria-hidden="true" className="h-4 w-4" />
                {t("logout")}
              </button>
            </form>
          ) : null}
        </div>
        <div className="mt-10 grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          {entrypoints.map((entrypoint) => {
            const Icon = entrypoint.icon;
            return (
              <a
                key={entrypoint.key}
                href={entrypoint.href}
                className="group rounded-lg border border-zinc-200 bg-white p-5 shadow-sm transition hover:border-emerald-500"
              >
                <Icon aria-hidden="true" className="h-6 w-6 text-emerald-700" />
                <div className="mt-5 flex items-center justify-between">
                  <h2 className="text-xl font-semibold">
                    {t(`${entrypoint.key}.title`)}
                  </h2>
                  <ArrowRight
                    aria-hidden="true"
                    className="h-5 w-5 transition group-hover:translate-x-1"
                  />
                </div>
                <p className="mt-3 text-sm leading-6 text-zinc-600">
                  {t(`${entrypoint.key}.description`)}
                </p>
              </a>
            );
          })}
        </div>
      </section>
    </main>
  );
}
