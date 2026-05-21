// Profile settings page for Auth.js session details, feature flags, and
// integration mock/real mode visibility.
import {
  CheckCircle2,
  ExternalLink,
  KeyRound,
  LogOut,
  ServerCog,
  ShieldCheck,
  Sparkles,
  UserRound,
  XCircle,
} from "lucide-react";
import NextLink from "next/link";
import { getTranslations } from "next-intl/server";

import { ApiUnavailable } from "@/components/system/api-unavailable";
import { Link } from "@/i18n/navigation";
import { localizedPath } from "@/i18n/paths";
import { auth, signOut } from "@/lib/auth";
import { createPrompteerApiClient, unwrapApiResponse } from "@/lib/api-client";
import { getServerEnv } from "@/lib/env";
import { normalizeError } from "@/lib/errors";

export const dynamic = "force-dynamic";

type Props = {
  params: Promise<{ locale: string }>;
};

export default async function ProfilePage({
  params,
}: Props): Promise<React.ReactElement> {
  const { locale } = await params;
  async function signOutAction(): Promise<void> {
    "use server";

    await signOut({ redirectTo: localizedPath("/login", locale) });
  }

  const t = await getTranslations("profile");
  const errors = await getTranslations("errors");
  const session = await auth();

  if (!session?.user) {
    return (
      <main className="min-h-screen bg-zinc-50 px-6 py-8 text-zinc-950">
        <section className="mx-auto grid min-h-[calc(100vh-4rem)] max-w-xl place-items-center">
          <div className="w-full rounded-lg border border-zinc-200 bg-white p-6 shadow-sm">
            <UserRound
              aria-hidden="true"
              className="h-8 w-8 text-emerald-700"
            />
            <h1 className="mt-5 text-2xl font-semibold">
              {t("signedOutTitle")}
            </h1>
            <p className="mt-3 text-sm leading-6 text-zinc-600">
              {t("signedOutDescription")}
            </p>
            <Link
              className="mt-5 inline-flex min-h-11 items-center gap-2 rounded-md bg-zinc-950 px-4 text-sm font-medium text-white transition hover:bg-zinc-800"
              href="/login"
            >
              <ExternalLink aria-hidden="true" className="h-4 w-4" />
              {t("signIn")}
            </Link>
          </div>
        </section>
      </main>
    );
  }

  const api = createPrompteerApiClient();
  let features: { llm: boolean; payments: boolean; email: boolean };
  let integrations: {
    google_oauth: string;
    llm: string;
    payments: string;
    email: string;
  };

  try {
    const [featuresResult, integrationsResult] = await Promise.all([
      api.GET("/api/v1/config/features", { cache: "no-store" }),
      api.GET("/api/v1/config/integrations", { cache: "no-store" }),
    ]);
    features = unwrapApiResponse(featuresResult);
    integrations = unwrapApiResponse(integrationsResult);
  } catch (error) {
    const normalizedError = await normalizeError(error);
    return (
      <main className="min-h-screen bg-zinc-50 px-6 py-8 text-zinc-950">
        <section className="mx-auto max-w-6xl">
          <ApiUnavailable
            actionLabel={errors("reload")}
            description={errors("apiUnavailableDescription")}
            error={normalizedError}
            requestIdLabel={errors("requestId")}
            title={errors("apiUnavailableTitle")}
          />
        </section>
      </main>
    );
  }
  const serverEnv = getServerEnv();
  const featureRows = [
    { label: t("features.llm"), enabled: features.llm },
    { label: t("features.payments"), enabled: features.payments },
    { label: t("features.email"), enabled: features.email },
  ];
  const integrationRows = [
    { label: t("integrations.google"), mode: integrations.google_oauth },
    { label: t("integrations.llm"), mode: integrations.llm },
    { label: t("integrations.stripe"), mode: integrations.payments },
    { label: t("integrations.sendgrid"), mode: integrations.email },
  ];
  const securityRows = [
    { label: t("security.jwks"), value: "/api/auth/jwks" },
    {
      label: t("security.audience"),
      value: serverEnv.AUTH_JWT_AUDIENCE,
    },
    {
      label: t("security.issuer"),
      value: serverEnv.AUTH_JWT_ISSUER ?? serverEnv.AUTH_URL,
    },
  ];

  return (
    <main className="min-h-screen bg-zinc-50 px-6 py-8 text-zinc-950">
      <section className="mx-auto max-w-6xl">
        <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
          <div>
            <p className="text-sm font-semibold uppercase text-emerald-700">
              {t("eyebrow")}
            </p>
            <h1 className="mt-2 text-3xl font-semibold">{t("title")}</h1>
            <p className="mt-3 max-w-2xl text-sm leading-6 text-zinc-600">
              {t("description")}
            </p>
          </div>
          <form action={signOutAction}>
            <button
              className="inline-flex min-h-11 items-center gap-2 rounded-md border border-zinc-300 bg-white px-4 text-sm font-medium text-zinc-900 transition hover:bg-zinc-50"
              type="submit"
            >
              <LogOut aria-hidden="true" className="h-4 w-4" />
              {t("logout")}
            </button>
          </form>
        </div>

        <div className="mt-8 grid gap-6 lg:grid-cols-[minmax(0,0.9fr)_minmax(0,1.1fr)]">
          <section className="rounded-lg border border-zinc-200 bg-white p-6 shadow-sm">
            <div className="flex items-start gap-3">
              <UserRound
                aria-hidden="true"
                className="mt-1 h-5 w-5 text-emerald-700"
              />
              <div>
                <h2 className="text-xl font-semibold">{t("account.title")}</h2>
                <p className="mt-2 text-sm leading-6 text-zinc-600">
                  {t("account.description")}
                </p>
              </div>
            </div>
            <dl className="mt-6 grid gap-3 text-sm">
              <div className="flex items-center justify-between gap-4 border-t border-zinc-200 pt-3">
                <dt className="text-zinc-500">{t("account.name")}</dt>
                <dd className="truncate font-medium text-zinc-950">
                  {session.user.name ?? t("account.fallbackName")}
                </dd>
              </div>
              <div className="flex items-center justify-between gap-4 border-t border-zinc-200 pt-3">
                <dt className="text-zinc-500">{t("account.email")}</dt>
                <dd className="truncate font-medium text-zinc-950">
                  {session.user.email ?? t("account.fallbackEmail")}
                </dd>
              </div>
            </dl>
          </section>

          <section className="rounded-lg border border-zinc-200 bg-white p-6 shadow-sm">
            <div className="flex items-start gap-3">
              <ServerCog
                aria-hidden="true"
                className="mt-1 h-5 w-5 text-emerald-700"
              />
              <div>
                <h2 className="text-xl font-semibold">{t("features.title")}</h2>
                <p className="mt-2 text-sm leading-6 text-zinc-600">
                  {t("features.description")}
                </p>
              </div>
            </div>
            <dl className="mt-6 grid gap-3 text-sm">
              {featureRows.map((feature) => (
                <div
                  className="flex items-center justify-between gap-4 border-t border-zinc-200 pt-3"
                  key={feature.label}
                >
                  <dt className="text-zinc-500">{feature.label}</dt>
                  <dd className="inline-flex items-center gap-2 font-medium text-zinc-950">
                    <span>
                      {feature.enabled
                        ? t("features.enabled")
                        : t("features.disabled")}
                    </span>
                    {feature.enabled ? (
                      <CheckCircle2
                        aria-hidden="true"
                        className="h-4 w-4 text-emerald-700"
                      />
                    ) : (
                      <XCircle
                        aria-hidden="true"
                        className="h-4 w-4 text-amber-600"
                      />
                    )}
                  </dd>
                </div>
              ))}
            </dl>
          </section>
        </div>

        <div className="mt-6 grid gap-6 lg:grid-cols-3">
          <section className="rounded-lg border border-zinc-200 bg-white p-6 shadow-sm">
            <div className="flex items-start gap-3">
              <Sparkles
                aria-hidden="true"
                className="mt-1 h-5 w-5 text-emerald-700"
              />
              <div>
                <h2 className="text-xl font-semibold">
                  {t("integrations.title")}
                </h2>
                <p className="mt-2 text-sm leading-6 text-zinc-600">
                  {t("integrations.description")}
                </p>
              </div>
            </div>
            <dl className="mt-6 grid gap-3 text-sm">
              {integrationRows.map((integration) => (
                <div
                  className="flex items-center justify-between gap-4 border-t border-zinc-200 pt-3"
                  key={integration.label}
                >
                  <dt className="text-zinc-500">{integration.label}</dt>
                  <dd className="rounded-md border border-zinc-200 px-2 py-1 text-xs font-medium uppercase text-zinc-700">
                    {integration.mode === "real"
                      ? t("integrations.real")
                      : t("integrations.mock")}
                  </dd>
                </div>
              ))}
            </dl>
          </section>

          <section className="rounded-lg border border-zinc-200 bg-white p-6 shadow-sm">
            <div className="flex items-start gap-3">
              <ShieldCheck
                aria-hidden="true"
                className="mt-1 h-5 w-5 text-emerald-700"
              />
              <div>
                <h2 className="text-xl font-semibold">{t("security.title")}</h2>
                <p className="mt-2 text-sm leading-6 text-zinc-600">
                  {t("security.description")}
                </p>
              </div>
            </div>
            <dl className="mt-6 grid gap-3 text-sm">
              {securityRows.map((row) => (
                <div className="border-t border-zinc-200 pt-3" key={row.label}>
                  <dt className="text-zinc-500">{row.label}</dt>
                  <dd className="mt-1 break-all font-mono text-xs text-zinc-800">
                    {row.value}
                  </dd>
                </div>
              ))}
            </dl>
          </section>

          <section className="rounded-lg border border-zinc-200 bg-white p-6 shadow-sm">
            <div className="flex items-start gap-3">
              <KeyRound
                aria-hidden="true"
                className="mt-1 h-5 w-5 text-emerald-700"
              />
              <div>
                <h2 className="text-xl font-semibold">
                  {t("shortcuts.title")}
                </h2>
                <p className="mt-2 text-sm leading-6 text-zinc-600">
                  {t("shortcuts.description")}
                </p>
              </div>
            </div>
            <div className="mt-6 grid gap-2">
              <ShortcutLink
                href="/challenges/coding"
                label={t("shortcuts.coding")}
              />
              <ShortcutLink href="/billing" label={t("shortcuts.billing")} />
              <NextLink
                className="inline-flex min-h-11 items-center justify-between gap-3 rounded-md border border-zinc-300 px-3 text-sm font-medium text-zinc-900 transition hover:bg-zinc-50"
                href="/dev/mailbox"
              >
                <span>{t("shortcuts.mailbox")}</span>
                <ExternalLink
                  aria-hidden="true"
                  className="h-4 w-4 text-emerald-700"
                />
              </NextLink>
            </div>
          </section>
        </div>
      </section>
    </main>
  );
}

type ShortcutHref = "/challenges/coding" | "/billing";

function ShortcutLink({
  href,
  label,
}: {
  href: ShortcutHref;
  label: string;
}): React.ReactElement {
  return (
    <Link
      className="inline-flex min-h-11 items-center justify-between gap-3 rounded-md border border-zinc-300 px-3 text-sm font-medium text-zinc-900 transition hover:bg-zinc-50"
      href={href}
    >
      <span>{label}</span>
      <ExternalLink aria-hidden="true" className="h-4 w-4 text-emerald-700" />
    </Link>
  );
}
