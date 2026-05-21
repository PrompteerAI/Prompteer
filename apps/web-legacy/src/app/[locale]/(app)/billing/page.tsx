// Legacy-preview billing route that mirrors the old subscription screen.
import { LegacyBillingPanel } from "@/components/legacy/billing-panel";
import { readGatewaySession } from "@/lib/auth-gateway";
import { readBillingSubscription, readFeatures } from "@/lib/data";

export const dynamic = "force-dynamic";

type Props = {
  params: Promise<{ locale: string }>;
};

export default async function BillingPage({
  params,
}: Props): Promise<React.ReactElement> {
  const { locale } = await params;
  const [session, features] = await Promise.all([
    readGatewaySession(),
    readFeatures(),
  ]);
  const subscription = session?.user ? await readBillingSubscription() : null;
  const email = session?.user?.email ?? null;

  return (
    <main className="legacy-page">
      <section className="legacy-section-banner compact">
        <h1>Subscription checkout</h1>
        <p>Stripe-compatible billing flow in the legacy settings layout.</p>
      </section>
      <LegacyBillingPanel
        billingEmail={email}
        demoLoginHref={`/dev/login-as/paid%40prompteer.dev?locale=${locale}`}
        initialSubscription={subscription}
        isAuthenticated={Boolean(session?.user)}
        loginHref={`/${locale}/login`}
        paymentsEnabled={features.payments}
      />
    </main>
  );
}
