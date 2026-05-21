// Client-side billing checkout panel for mock and hosted Stripe flows.
"use client";

// Interactive checkout exercise for the local Stripe-compatible billing mock.
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  CheckCircle2,
  CreditCard,
  ExternalLink,
  Loader2,
  RotateCcw,
} from "lucide-react";
import { useLocale, useTranslations } from "next-intl";
import { useMemo, useState } from "react";

import { Badge, Button, Card } from "@/components/ui";
import { createPrompteerApiClient, unwrapApiResponse } from "@/lib/api-client";
import { normalizeError } from "@/lib/errors";
import type { components } from "@prompteer/shared-types";

type CheckoutSession = components["schemas"]["CheckoutSessionRead"];
type BillingSubscription = components["schemas"]["BillingSubscriptionRead"];

type CheckoutStep = "idle" | "created" | "complete";

interface BillingCheckoutPanelProps {
  billingEmail: string;
  initialSubscription: BillingSubscription | null;
  paymentsEnabled: boolean;
}

export function BillingCheckoutPanel({
  billingEmail,
  initialSubscription,
  paymentsEnabled,
}: BillingCheckoutPanelProps): React.ReactElement {
  const locale = useLocale();
  const t = useTranslations("billing");
  const queryClient = useQueryClient();
  const [session, setSession] = useState<CheckoutSession | null>(null);
  const [step, setStep] = useState<CheckoutStep>("idle");
  const [error, setError] = useState<string | null>(null);
  const subscriptionQueryKey = useMemo(
    () => ["billing", "subscription", billingEmail] as const,
    [billingEmail],
  );
  const subscriptionQuery = useQuery({
    queryKey: subscriptionQueryKey,
    queryFn: readBillingSubscription,
    enabled: paymentsEnabled,
    initialData: initialSubscription ?? undefined,
    staleTime: 10_000,
  });
  const subscription = subscriptionQuery.data ?? null;
  const isMockSession = session?.provider === "mock";
  const checkoutIsPaid = session?.payment_status === "paid";
  const accountHasActiveSubscription = subscription?.status === "active";
  const hasActiveSubscription = checkoutIsPaid || accountHasActiveSubscription;
  const hostedCheckoutUrl =
    session && !isMockSession && session.url ? session.url : null;
  const createCheckoutMutation = useMutation({
    mutationKey: ["billing", "checkout", "create", billingEmail],
    mutationFn: createCheckoutSession,
  });
  const completeCheckoutMutation = useMutation({
    mutationKey: ["billing", "checkout", "complete", session?.id],
    mutationFn: completeCheckoutSession,
  });
  const isLoading =
    createCheckoutMutation.isPending ||
    completeCheckoutMutation.isPending ||
    subscriptionQuery.isLoading;
  const providerLabel =
    session?.provider ?? subscription?.provider ?? t("plan.fallbackProvider");
  const accountEmail =
    session?.customer_email ?? subscription?.customer_email ?? billingEmail;
  const paymentStatusLabel =
    session?.payment_status ??
    (hasActiveSubscription
      ? t("checkout.activePaymentStatus")
      : t("checkout.fallbackPaymentStatus"));
  const checkoutStatusLabel =
    session?.status ??
    (hasActiveSubscription
      ? t("checkout.activeStatus")
      : t("checkout.fallbackStatus"));
  const checkoutSessionLabel =
    session?.id ??
    (hasActiveSubscription
      ? t("checkout.persistedSession")
      : t("checkout.fallbackSession"));
  const checkoutDescription = session
    ? isMockSession
      ? t("checkout.readyDescription")
      : t("checkout.hostedDescription")
    : hasActiveSubscription
      ? t("checkout.activeDescription")
      : t("checkout.createDescription");
  const startCheckoutLabel = accountHasActiveSubscription
    ? t("checkout.startAnother")
    : t("checkout.start");
  const paymentStatusVariant = session
    ? checkoutIsPaid
      ? "success"
      : "warning"
    : accountHasActiveSubscription
      ? "success"
      : "secondary";

  const price = useMemo(() => {
    if (!session?.amount_total || !session.currency) {
      return t("plan.fallbackPrice");
    }
    return new Intl.NumberFormat(locale, {
      style: "currency",
      currency: session.currency.toUpperCase(),
    }).format(session.amount_total / 100);
  }, [locale, session, t]);

  async function createCheckout(): Promise<void> {
    if (!paymentsEnabled) {
      setError(t("errors.disabled"));
      return;
    }
    setError(null);
    try {
      const response = await createCheckoutMutation.mutateAsync();
      setSession(response);
      setStep("created");
    } catch (caughtError) {
      const normalizedError = await normalizeError(caughtError);
      if (normalizedError.code === "rate_limited") {
        setError(t("errors.rateLimited"));
      } else if (normalizedError.status === 401) {
        setError(t("errors.startUnauthorized"));
      } else {
        setError(t("errors.startFailed"));
      }
    }
  }

  async function completeCheckout(): Promise<void> {
    if (!session) {
      return;
    }
    if (!paymentsEnabled) {
      setError(t("errors.disabled"));
      return;
    }
    setError(null);
    try {
      const response = await completeCheckoutMutation.mutateAsync(session.id);
      setSession(response);
      setStep("complete");
      queryClient.setQueryData<BillingSubscription>(subscriptionQueryKey, {
        plan: "paid",
        status: "active",
        customer_email: response.customer_email ?? billingEmail,
        provider: response.provider,
      });
    } catch (caughtError) {
      const normalizedError = await normalizeError(caughtError);
      if (normalizedError.code === "rate_limited") {
        setError(t("errors.rateLimited"));
      } else if (normalizedError.status === 401) {
        setError(t("errors.completeUnauthorized"));
      } else {
        setError(t("errors.completeFailed"));
      }
    }
  }

  function reset(): void {
    setSession(null);
    setStep("idle");
    setError(null);
  }

  return (
    <section className="grid gap-6 lg:grid-cols-[minmax(0,0.85fr)_minmax(0,1.15fr)]">
      <Card className="p-6">
        <p className="text-sm font-medium uppercase text-emerald-700">
          {t("plan.name")}
        </p>
        <h2 className="mt-2 text-3xl font-semibold text-zinc-950">
          {t("plan.price")}
        </h2>
        <p className="mt-4 text-sm leading-6 text-zinc-600">
          {t("plan.description")}
        </p>
        <dl className="mt-6 grid gap-3 text-sm">
          <div className="flex items-center justify-between border-t border-zinc-200 pt-3">
            <dt className="text-zinc-500">{t("plan.provider")}</dt>
            <dd className="font-medium capitalize text-zinc-950">
              {providerLabel}
            </dd>
          </div>
          <div className="flex items-center justify-between border-t border-zinc-200 pt-3">
            <dt className="text-zinc-500">{t("plan.billingEmail")}</dt>
            <dd className="font-medium text-zinc-950">{accountEmail}</dd>
          </div>
        </dl>
      </Card>

      <Card className="p-6">
        <div className="flex items-start justify-between gap-4">
          <div>
            <h2 className="text-xl font-semibold text-zinc-950">
              {t("checkout.title")}
            </h2>
            <p className="mt-2 text-sm leading-6 text-zinc-600">
              {checkoutDescription}
            </p>
          </div>
          <Badge className="capitalize" variant={paymentStatusVariant}>
            {paymentStatusLabel}
          </Badge>
        </div>

        <div className="mt-6 rounded-lg border border-border bg-surface-subtle p-4">
          <dl className="grid gap-3 text-sm sm:grid-cols-2">
            <div>
              <dt className="text-zinc-500">{t("checkout.amount")}</dt>
              <dd className="mt-1 font-medium text-zinc-950">{price}</dd>
            </div>
            <div>
              <dt className="text-zinc-500">{t("checkout.status")}</dt>
              <dd className="mt-1 font-medium capitalize text-zinc-950">
                {checkoutStatusLabel}
              </dd>
            </div>
            <div className="sm:col-span-2">
              <dt className="text-zinc-500">{t("checkout.session")}</dt>
              <dd className="mt-1 break-all font-mono text-xs text-zinc-700">
                {checkoutSessionLabel}
              </dd>
            </div>
            {hostedCheckoutUrl ? (
              <div className="sm:col-span-2">
                <dt className="text-zinc-500">{t("checkout.hostedUrl")}</dt>
                <dd className="mt-1 break-all font-mono text-xs text-zinc-700">
                  {hostedCheckoutUrl}
                </dd>
              </div>
            ) : null}
          </dl>
        </div>

        <div className="mt-5 flex flex-wrap gap-3">
          <Button
            className="min-h-11 px-4"
            aria-busy={createCheckoutMutation.isPending}
            disabled={!paymentsEnabled || isLoading}
            onClick={() => {
              void createCheckout();
            }}
            type="button"
            variant={accountHasActiveSubscription ? "outline" : "default"}
          >
            {createCheckoutMutation.isPending ? (
              <Loader2 aria-hidden="true" className="h-4 w-4 animate-spin" />
            ) : accountHasActiveSubscription ? (
              <CheckCircle2 aria-hidden="true" className="h-4 w-4" />
            ) : (
              <CreditCard aria-hidden="true" className="h-4 w-4" />
            )}
            {startCheckoutLabel}
          </Button>
          {hostedCheckoutUrl ? (
            <a
              className="inline-flex min-h-11 items-center gap-2 rounded-md border border-zinc-300 px-4 text-sm font-medium text-zinc-900 transition hover:bg-zinc-50"
              href={hostedCheckoutUrl}
              rel="noreferrer"
              target="_blank"
            >
              <ExternalLink aria-hidden="true" className="h-4 w-4" />
              {t("checkout.openHosted")}
            </a>
          ) : (
            <Button
              className="min-h-11 border-emerald-700 bg-emerald-50 px-4 text-emerald-900 hover:bg-emerald-100 disabled:border-zinc-300 disabled:bg-white disabled:text-zinc-400"
              aria-busy={completeCheckoutMutation.isPending}
              disabled={
                !paymentsEnabled ||
                !session ||
                session.status === "complete" ||
                isLoading
              }
              onClick={() => {
                void completeCheckout();
              }}
              type="button"
              variant="outline"
            >
              {completeCheckoutMutation.isPending ? (
                <Loader2 aria-hidden="true" className="h-4 w-4 animate-spin" />
              ) : (
                <CheckCircle2 aria-hidden="true" className="h-4 w-4" />
              )}
              {t("checkout.complete")}
            </Button>
          )}
          {session || step !== "idle" ? (
            <Button
              className="min-h-11 px-4"
              onClick={reset}
              type="button"
              variant="outline"
            >
              <RotateCcw aria-hidden="true" className="h-4 w-4" />
              {t("checkout.reset")}
            </Button>
          ) : null}
        </div>

        {!paymentsEnabled ? (
          <p className="mt-3 text-sm text-amber-700">
            {t("checkout.disabledNotice")}
          </p>
        ) : null}

        {error ? (
          <p className="mt-4 text-sm text-red-600" role="alert">
            {error}
          </p>
        ) : null}

        {hasActiveSubscription ? (
          <div
            aria-live="polite"
            className="mt-6 rounded-lg border border-emerald-200 bg-emerald-50 p-4 text-sm leading-6 text-emerald-900"
          >
            {step === "complete"
              ? t.rich("checkout.completed", {
                  email: accountEmail,
                  event: (chunks) => <code>{chunks}</code>,
                })
              : t("checkout.persistedActive", { email: accountEmail })}
          </div>
        ) : null}
      </Card>
    </section>
  );
}

async function readBillingSubscription(): Promise<BillingSubscription> {
  const api = createPrompteerApiClient();
  return unwrapApiResponse(await api.GET("/api/v1/billing/subscription"));
}

async function createCheckoutSession(): Promise<CheckoutSession> {
  const api = createPrompteerApiClient();
  return unwrapApiResponse(
    await api.POST("/api/v1/billing/checkout", {
      body: {
        plan: "pro_monthly",
      },
    }),
  );
}

async function completeCheckoutSession(
  sessionId: string,
): Promise<CheckoutSession> {
  const api = createPrompteerApiClient();
  return unwrapApiResponse(
    await api.POST("/api/v1/billing/checkout/{session_id}/complete", {
      params: { path: { session_id: sessionId } },
    }),
  );
}
