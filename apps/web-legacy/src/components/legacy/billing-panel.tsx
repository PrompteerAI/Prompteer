// Client-side legacy-preview billing panel for mock checkout flows.
"use client";

import {
  CheckCircle2,
  CreditCard,
  Loader2,
  LogIn,
  RotateCcw,
} from "lucide-react";
import { useTranslations } from "next-intl";
import { useState } from "react";

import { createPrompteerApiClient, unwrapApiResponse } from "@/lib/api-client";
import { normalizeError } from "@/lib/errors";
import type { components } from "@prompteer/shared-types";

type CheckoutSession = components["schemas"]["CheckoutSessionRead"];
type BillingSubscription = components["schemas"]["BillingSubscriptionRead"];

interface LegacyBillingPanelProps {
  billingEmail: string | null;
  demoLoginHref: string;
  initialSubscription: BillingSubscription | null;
  isAuthenticated: boolean;
  loginHref: string;
  paymentsEnabled: boolean;
}

export function LegacyBillingPanel({
  billingEmail,
  demoLoginHref,
  initialSubscription,
  isAuthenticated,
  loginHref,
  paymentsEnabled,
}: LegacyBillingPanelProps): React.ReactElement {
  const t = useTranslations("legacy.billing.panel");
  const commonT = useTranslations("legacy.common");
  const [session, setSession] = useState<CheckoutSession | null>(null);
  const [subscription, setSubscription] = useState<BillingSubscription | null>(
    initialSubscription,
  );
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const checkoutPaid = session?.payment_status === "paid";
  const canStartCheckout =
    paymentsEnabled && isAuthenticated && Boolean(billingEmail) && !isLoading;

  async function startCheckout(): Promise<void> {
    if (!isAuthenticated || !billingEmail) {
      setError(t("errors.signInBeforeCheckout"));
      return;
    }
    setError(null);
    setIsLoading(true);
    try {
      const api = createPrompteerApiClient();
      const response = unwrapApiResponse(
        await api.POST("/api/v1/billing/checkout", {
          body: {
            plan: "pro_monthly",
          },
        }),
      );
      setSession(response);
    } catch (caughtError) {
      const normalized = await normalizeError(caughtError);
      setError(
        normalized.status === 401
          ? t("errors.signInBeforeCheckout")
          : normalized.message,
      );
    } finally {
      setIsLoading(false);
    }
  }

  async function completeCheckout(): Promise<void> {
    if (!session || !billingEmail) {
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
        <span className="legacy-pill">{t("planName")}</span>
        <h2 style={{ fontSize: 32, marginTop: 12 }}>{t("planPrice")}</h2>
        <p>{t("planDescription")}</p>
        <dl>
          <div className="legacy-card-meta">
            <dt>{t("provider")}</dt>
            <dd>
              {session?.provider ??
                subscription?.provider ??
                t("fallbackProvider")}
            </dd>
          </div>
          <div className="legacy-card-meta">
            <dt>{t("billingEmail")}</dt>
            <dd>
              {session?.customer_email ??
                subscription?.customer_email ??
                billingEmail ??
                commonT("signInRequired")}
            </dd>
          </div>
        </dl>
      </aside>
      <div className="legacy-panel">
        <div className="legacy-card-meta">
          <h2>{t("checkoutTitle")}</h2>
          <span className="legacy-pill">
            {checkoutPaid ? t("paid") : t("unpaid")}
          </span>
        </div>
        <p>{t("checkoutDescription")}</p>
        <dl style={{ marginTop: 22 }}>
          <div className="legacy-card-meta">
            <dt>{t("status")}</dt>
            <dd>{session?.status ?? t("fallbackStatus")}</dd>
          </div>
          <div className="legacy-card-meta">
            <dt>{t("session")}</dt>
            <dd style={{ fontFamily: "monospace", overflowWrap: "anywhere" }}>
              {session?.id ?? t("fallbackSession")}
            </dd>
          </div>
        </dl>
        <div
          style={{ display: "flex", flexWrap: "wrap", gap: 12, marginTop: 22 }}
        >
          {isAuthenticated ? (
            <button
              className="legacy-primary-button"
              disabled={!canStartCheckout}
              onClick={() => void startCheckout()}
              type="button"
            >
              {isLoading ? (
                <Loader2 aria-hidden="true" size={18} />
              ) : (
                <CreditCard aria-hidden="true" size={18} />
              )}
              {t("startCheckout")}
            </button>
          ) : (
            <div className="legacy-login-callout compact" role="note">
              <p>{t("loginCallout")}</p>
              <div className="legacy-auth-inline-actions">
                <a className="legacy-primary-button" href={demoLoginHref}>
                  <LogIn aria-hidden="true" size={18} />
                  {commonT("paidDemoLogin")}
                </a>
                <a className="legacy-secondary-button" href={loginHref}>
                  {commonT("primaryLogin")}
                </a>
              </div>
            </div>
          )}
          <button
            className="legacy-secondary-button"
            disabled={
              !paymentsEnabled ||
              !isAuthenticated ||
              !billingEmail ||
              isLoading ||
              !session ||
              session.status === "complete"
            }
            onClick={() => void completeCheckout()}
            type="button"
          >
            <CheckCircle2 aria-hidden="true" size={18} />
            {t("completeCheckout")}
          </button>
          <button
            className="legacy-secondary-button"
            disabled={!isAuthenticated}
            onClick={() => {
              setSession(null);
              setError(null);
            }}
            type="button"
          >
            <RotateCcw aria-hidden="true" size={18} />
            {t("reset")}
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
