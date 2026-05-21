"use client";

import { CheckCircle2, CreditCard, Loader2, RotateCcw } from "lucide-react";
import { useState } from "react";

import { createPrompteerApiClient, unwrapApiResponse } from "@/lib/api-client";
import { normalizeError } from "@/lib/errors";
import type { components } from "@prompteer/shared-types";

type CheckoutSession = components["schemas"]["CheckoutSessionRead"];
type BillingSubscription = components["schemas"]["BillingSubscriptionRead"];

interface LegacyBillingPanelProps {
  billingEmail: string;
  initialSubscription: BillingSubscription | null;
  paymentsEnabled: boolean;
}

export function LegacyBillingPanel({
  billingEmail,
  initialSubscription,
  paymentsEnabled,
}: LegacyBillingPanelProps): React.ReactElement {
  const [session, setSession] = useState<CheckoutSession | null>(null);
  const [subscription, setSubscription] = useState<BillingSubscription | null>(
    initialSubscription,
  );
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const active =
    session?.payment_status === "paid" || subscription?.status === "active";

  async function startCheckout(): Promise<void> {
    setError(null);
    setIsLoading(true);
    try {
      const api = createPrompteerApiClient();
      const response = unwrapApiResponse(
        await api.POST("/api/v1/billing/checkout", {
          body: {
            customer_email: billingEmail,
            plan: "pro_monthly",
          },
        }),
      );
      setSession(response);
    } catch (caughtError) {
      const normalized = await normalizeError(caughtError);
      setError(
        normalized.status === 401
          ? "Sign in before starting checkout."
          : normalized.message,
      );
    } finally {
      setIsLoading(false);
    }
  }

  async function completeCheckout(): Promise<void> {
    if (!session) {
      return;
    }
    setError(null);
    setIsLoading(true);
    try {
      const api = createPrompteerApiClient();
      const response = unwrapApiResponse(
        await api.POST("/api/v1/billing/checkout/{session_id}/complete", {
          params: { path: { session_id: session.id } },
        }),
      );
      setSession(response);
      setSubscription({
        customer_email: response.customer_email ?? billingEmail,
        plan: "paid",
        provider: response.provider,
        status: "active",
      });
    } catch (caughtError) {
      const normalized = await normalizeError(caughtError);
      setError(normalized.message);
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <section className="legacy-billing-grid">
      <aside className="legacy-panel">
        <span className="legacy-pill">Prompteer Pro</span>
        <h2 style={{ fontSize: 32, marginTop: 12 }}>$12/mo</h2>
        <p>
          Start and complete a Stripe-shaped checkout while preserving the old
          settings-style panel layout.
        </p>
        <dl>
          <div className="legacy-card-meta">
            <dt>Provider</dt>
            <dd>{session?.provider ?? subscription?.provider ?? "mock"}</dd>
          </div>
          <div className="legacy-card-meta">
            <dt>Billing email</dt>
            <dd>
              {session?.customer_email ??
                subscription?.customer_email ??
                billingEmail}
            </dd>
          </div>
        </dl>
      </aside>
      <div className="legacy-panel">
        <div className="legacy-card-meta">
          <h2>Checkout session</h2>
          <span className="legacy-pill">{active ? "paid" : "unpaid"}</span>
        </div>
        <p>
          Local mock sessions complete in-app. Real Stripe sessions return a
          hosted URL from the API.
        </p>
        <dl style={{ marginTop: 22 }}>
          <div className="legacy-card-meta">
            <dt>Status</dt>
            <dd>{session?.status ?? (active ? "active" : "not created")}</dd>
          </div>
          <div className="legacy-card-meta">
            <dt>Session</dt>
            <dd style={{ fontFamily: "monospace", overflowWrap: "anywhere" }}>
              {session?.id ?? "No checkout session yet"}
            </dd>
          </div>
        </dl>
        <div
          style={{ display: "flex", flexWrap: "wrap", gap: 12, marginTop: 22 }}
        >
          <button
            className="legacy-primary-button"
            disabled={!paymentsEnabled || isLoading}
            onClick={() => void startCheckout()}
            type="button"
          >
            {isLoading ? (
              <Loader2 aria-hidden="true" size={18} />
            ) : (
              <CreditCard aria-hidden="true" size={18} />
            )}
            Start checkout
          </button>
          <button
            className="legacy-secondary-button"
            disabled={
              !paymentsEnabled ||
              isLoading ||
              !session ||
              session.status === "complete"
            }
            onClick={() => void completeCheckout()}
            type="button"
          >
            <CheckCircle2 aria-hidden="true" size={18} />
            Complete mock checkout
          </button>
          <button
            className="legacy-secondary-button"
            onClick={() => {
              setSession(null);
              setError(null);
            }}
            type="button"
          >
            <RotateCcw aria-hidden="true" size={18} />
            Reset
          </button>
        </div>
        {error ? (
          <p role="alert" style={{ color: "#c92a2a" }}>
            {error}
          </p>
        ) : null}
      </div>
    </section>
  );
}
