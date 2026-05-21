// Billing page for exercising the local Stripe-compatible checkout flow.
import { getTranslations } from "next-intl/server";

import { BillingCheckoutPanel } from "@/components/billing/billing-checkout-panel";
import { auth } from "@/lib/auth";
import { createPrompteerApiClient, unwrapApiResponse } from "@/lib/api-client";
import { apiTokenForSession } from "@/server/api-token";

export const dynamic = "force-dynamic";

export default async function BillingPage(): Promise<React.ReactElement> {
  const [t, session] = await Promise.all([getTranslations("billing"), auth()]);
  const billingEmail = session?.user?.email ?? "paid@prompteer.dev";
  const api = createPrompteerApiClient();
  const [featuresResult, subscriptionResult] = await Promise.all([
    api.GET("/api/v1/config/features", {
      cache: "no-store",
    }),
    session?.user?.email
      ? api.GET("/api/v1/billing/subscription", {
          cache: "no-store",
          headers: {
            authorization: `Bearer ${apiTokenForSession(session)}`,
          },
        })
      : null,
  ]);
  const features = unwrapApiResponse(featuresResult);
  const subscription = subscriptionResult
    ? unwrapApiResponse(subscriptionResult)
    : null;

  return (
    <main className="min-h-screen bg-zinc-50 px-6 py-8 text-zinc-950">
      <div className="mx-auto max-w-6xl">
        <div className="mb-6">
          <p className="text-sm font-semibold uppercase text-emerald-700">
            {t("eyebrow")}
          </p>
          <h1 className="mt-2 text-3xl font-semibold">{t("title")}</h1>
          <p className="mt-3 max-w-2xl text-sm leading-6 text-zinc-600">
            {t("description")}
          </p>
        </div>
        <BillingCheckoutPanel
          billingEmail={billingEmail}
          initialSubscription={subscription}
          paymentsEnabled={features.payments}
        />
      </div>
    </main>
  );
}
