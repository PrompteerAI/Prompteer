import { ArrowRight, Code2, CreditCard, LogIn } from "lucide-react";
import Link from "next/link";
import { getTranslations } from "next-intl/server";

const entrypoints = [
  { key: "login", icon: LogIn, href: "/en/login" },
  { key: "coding", icon: Code2, href: "/en/challenges/coding" },
  { key: "billing", icon: CreditCard, href: "/en/billing" },
] as const;

export default async function HomePage(): Promise<React.ReactElement> {
  const t = await getTranslations("home");

  return (
    <main className="min-h-screen bg-zinc-50 text-zinc-950">
      <section className="mx-auto w-full max-w-6xl px-6 py-8">
        <div className="max-w-3xl">
          <p className="text-sm font-semibold uppercase text-emerald-700">
            Prompteer
          </p>
          <h1 className="mt-4 text-5xl font-semibold leading-tight text-zinc-950">
            {t("title")}
          </h1>
          <p className="mt-5 max-w-2xl text-lg leading-8 text-zinc-600">
            {t("subtitle")}
          </p>
        </div>
        <div className="mt-10 grid gap-4 md:grid-cols-3">
          {entrypoints.map((entrypoint) => {
            const Icon = entrypoint.icon;
            return (
              <Link
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
              </Link>
            );
          })}
        </div>
      </section>
    </main>
  );
}
