import { BillingCheckoutPanel } from "@/components/billing/billing-checkout-panel";
import { apiGet } from "@/lib/api-client";
import type { FeatureFlags } from "@prompteer/shared-types";

export const dynamic = "force-dynamic";

export default async function BillingPage(): Promise<React.ReactElement> {
  const features = await apiGet<FeatureFlags>("/config/features", {
    cache: "no-store",
  });

  return (
    <main className="min-h-screen bg-zinc-50 px-6 py-8 text-zinc-950">
      <div className="mx-auto max-w-6xl">
        <div className="mb-6">
          <p className="text-sm font-semibold uppercase text-emerald-700">
            Billing
          </p>
          <h1 className="mt-2 text-3xl font-semibold">Subscription checkout</h1>
          <p className="mt-3 max-w-2xl text-sm leading-6 text-zinc-600">
            Start a Pro checkout session for the paid demo account and complete
            it through the local Stripe flow.
          </p>
        </div>
        <BillingCheckoutPanel paymentsEnabled={features.payments} />
      </div>
    </main>
  );
}
