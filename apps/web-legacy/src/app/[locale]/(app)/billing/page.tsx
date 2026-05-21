import { LegacyBillingPanel } from "@/components/legacy/billing-panel";
import { readGatewaySession } from "@/lib/auth-gateway";
import { readFeatures } from "@/lib/data";

export const dynamic = "force-dynamic";

export default async function BillingPage(): Promise<React.ReactElement> {
  const [session, features] = await Promise.all([
    readGatewaySession(),
    readFeatures(),
  ]);
  const email = session?.user?.email ?? "paid@prompteer.dev";

  return (
    <main className="legacy-page">
      <section className="legacy-section-banner compact">
        <h1>Subscription checkout</h1>
        <p>Stripe-compatible billing flow in the legacy settings layout.</p>
      </section>
      <LegacyBillingPanel
        billingEmail={email}
        initialSubscription={null}
        paymentsEnabled={features.payments}
      />
    </main>
  );
}
