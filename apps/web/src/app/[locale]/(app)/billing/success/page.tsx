// Stripe Checkout return page. It reconciles the hosted session before sending
// users back to their billing overview.
import { CheckCircle2, Clock, CreditCard } from "lucide-react";
import { getTranslations } from "next-intl/server";

import { Link } from "@/i18n/navigation";
import { auth } from "@/lib/auth";
import { createPrompteerApiClient, unwrapApiResponse } from "@/lib/api-client";
import { normalizeError } from "@/lib/errors";
import { apiTokenForSession } from "@/server/api-token";
import type { components } from "@prompteer/shared-types";

type CheckoutSession = components["schemas"]["CheckoutSessionRead"];

interface BillingSuccessPageProps {
  params: Promise<{ locale: string }>;
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}

export const dynamic = "force-dynamic";

export default async function BillingSuccessPage({
  params,
  searchParams,
}: BillingSuccessPageProps): Promise<React.ReactElement> {
  const [t, session, query, routeParams] = await Promise.all([
    getTranslations("billing.success"),
    auth(),
    searchParams,
    params,
  ]);
  const sessionId = firstSearchParam(query.session_id);

  if (!sessionId || !session?.user?.email) {
    return (
      <BillingSuccessShell backLabel={t("back")}>
        <StatusCard
          description={t("missingDescription")}
          Icon={Clock}
          title={t("missingTitle")}
          tone="amber"
        />
      </BillingSuccessShell>
    );
  }

  const api = createPrompteerApiClient();
  let checkoutSession: CheckoutSession;
  try {
    checkoutSession = unwrapApiResponse(
      await api.GET("/api/v1/billing/checkout/{session_id}", {
        cache: "no-store",
        headers: {
          authorization: `Bearer ${apiTokenForSession(session)}`,
        },
        params: { path: { session_id: sessionId } },
      }),
    );
  } catch (error) {
    const normalizedError = await normalizeError(error);
    return (
      <BillingSuccessShell backLabel={t("back")}>
        <StatusCard
          description={t("errorDescription", {
            requestId: normalizedError.requestId ?? t("unknownRequest"),
          })}
          Icon={Clock}
          title={t("errorTitle")}
          tone="red"
        />
      </BillingSuccessShell>
    );
  }

  const isComplete =
    checkoutSession.status === "complete" ||
    checkoutSession.payment_status === "paid";
  const amount =
    formatCheckoutAmount(checkoutSession, routeParams.locale) ??
    t("unknownAmount");

  return (
    <BillingSuccessShell backLabel={t("back")}>
      <StatusCard
        description={
          isComplete
            ? t("completeDescription", {
                email: checkoutSession.customer_email ?? session.user.email,
              })
            : t("pendingDescription")
        }
        Icon={isComplete ? CheckCircle2 : CreditCard}
        title={isComplete ? t("completeTitle") : t("pendingTitle")}
        tone={isComplete ? "emerald" : "amber"}
      />
      <dl className="mt-6 grid gap-3 rounded-lg border border-zinc-200 bg-white p-4 text-sm sm:grid-cols-2">
        <div>
          <dt className="text-zinc-500">{t("session")}</dt>
          <dd className="mt-1 break-all font-mono text-xs text-zinc-800">
            {checkoutSession.id}
          </dd>
        </div>
        <div>
          <dt className="text-zinc-500">{t("amount")}</dt>
          <dd className="mt-1 font-medium text-zinc-950">{amount}</dd>
        </div>
        <div>
          <dt className="text-zinc-500">{t("status")}</dt>
          <dd className="mt-1 font-medium capitalize text-zinc-950">
            {checkoutSession.status}
          </dd>
        </div>
        <div>
          <dt className="text-zinc-500">{t("paymentStatus")}</dt>
          <dd className="mt-1 font-medium capitalize text-zinc-950">
            {checkoutSession.payment_status}
          </dd>
        </div>
      </dl>
    </BillingSuccessShell>
  );
}

function BillingSuccessShell({
  backLabel,
  children,
}: {
  backLabel: string;
  children: React.ReactNode;
}): React.ReactElement {
  return (
    <main className="min-h-screen bg-zinc-50 px-6 py-8 text-zinc-950">
      <div className="mx-auto max-w-3xl">
        <div className="mb-6">
          <Link
            className="inline-flex min-h-10 items-center rounded-md border border-zinc-300 px-3 text-sm font-medium text-zinc-900 transition hover:bg-white"
            href="/billing"
          >
            {backLabel}
          </Link>
        </div>
        {children}
      </div>
    </main>
  );
}

function StatusCard({
  description,
  Icon,
  title,
  tone,
}: {
  description: string;
  Icon: typeof CheckCircle2;
  title: string;
  tone: "amber" | "emerald" | "red";
}): React.ReactElement {
  const toneClass = {
    amber: "border-amber-200 bg-amber-50 text-amber-900",
    emerald: "border-emerald-200 bg-emerald-50 text-emerald-900",
    red: "border-red-200 bg-red-50 text-red-900",
  }[tone];
  return (
    <section className={`rounded-lg border p-6 ${toneClass}`}>
      <Icon aria-hidden="true" className="h-6 w-6" />
      <h1 className="mt-4 text-2xl font-semibold">{title}</h1>
      <p className="mt-2 text-sm leading-6">{description}</p>
    </section>
  );
}

function firstSearchParam(value: string | string[] | undefined): string | null {
  if (Array.isArray(value)) {
    return value[0] ?? null;
  }
  return value ?? null;
}

function formatCheckoutAmount(
  session: CheckoutSession,
  locale: string,
): string | null {
  if (typeof session.amount_total !== "number" || !session.currency) {
    return null;
  }
  return new Intl.NumberFormat(locale, {
    style: "currency",
    currency: session.currency.toUpperCase(),
  }).format(session.amount_total / 100);
}
