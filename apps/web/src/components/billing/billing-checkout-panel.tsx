"use client";

import { CheckCircle2, CreditCard, Loader2, RotateCcw } from "lucide-react";
import { useMemo, useState } from "react";

import { apiPost } from "@/lib/api-client";

interface CheckoutSession {
  id: string;
  mode: string;
  status: string;
  payment_status: string;
  amount_total: number | null;
  currency: string | null;
  url: string | null;
  customer_email: string | null;
  provider: string;
}

type CheckoutStep = "idle" | "created" | "complete";

interface BillingCheckoutPanelProps {
  paymentsEnabled: boolean;
}

export function BillingCheckoutPanel({
  paymentsEnabled,
}: BillingCheckoutPanelProps): React.ReactElement {
  const [session, setSession] = useState<CheckoutSession | null>(null);
  const [step, setStep] = useState<CheckoutStep>("idle");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const price = useMemo(() => {
    if (!session?.amount_total || !session.currency) {
      return "$12.00";
    }
    return new Intl.NumberFormat("en", {
      style: "currency",
      currency: session.currency.toUpperCase(),
    }).format(session.amount_total / 100);
  }, [session]);

  async function createCheckout(): Promise<void> {
    if (!paymentsEnabled) {
      setError("Payments are disabled for this environment.");
      return;
    }
    setIsLoading(true);
    setError(null);
    try {
      const response = await apiPost<CheckoutSession>("/billing/checkout", {
        customer_email: "paid@prompteer.dev",
      });
      setSession(response);
      setStep("created");
    } catch {
      setError(
        "Checkout could not be started. Check that the API server is running.",
      );
    } finally {
      setIsLoading(false);
    }
  }

  async function completeCheckout(): Promise<void> {
    if (!session) {
      return;
    }
    if (!paymentsEnabled) {
      setError("Payments are disabled for this environment.");
      return;
    }
    setIsLoading(true);
    setError(null);
    try {
      const response = await apiPost<CheckoutSession>(
        `/billing/checkout/${session.id}/complete`,
        {},
      );
      setSession(response);
      setStep("complete");
    } catch {
      setError("Mock checkout could not be completed.");
    } finally {
      setIsLoading(false);
    }
  }

  function reset(): void {
    setSession(null);
    setStep("idle");
    setError(null);
  }

  return (
    <section className="grid gap-6 lg:grid-cols-[minmax(0,0.85fr)_minmax(0,1.15fr)]">
      <div className="rounded-lg border border-zinc-200 bg-white p-6 shadow-sm">
        <p className="text-sm font-medium uppercase text-emerald-700">
          Prompteer Pro
        </p>
        <h1 className="mt-2 text-3xl font-semibold text-zinc-950">$12/mo</h1>
        <p className="mt-4 text-sm leading-6 text-zinc-600">
          Use the paid demo account with a Stripe-shaped checkout session, local
          webhook completion, and deterministic subscription state.
        </p>
        <dl className="mt-6 grid gap-3 text-sm">
          <div className="flex items-center justify-between border-t border-zinc-200 pt-3">
            <dt className="text-zinc-500">Provider</dt>
            <dd className="font-medium capitalize text-zinc-950">
              {session?.provider ?? "mock"}
            </dd>
          </div>
          <div className="flex items-center justify-between border-t border-zinc-200 pt-3">
            <dt className="text-zinc-500">Billing email</dt>
            <dd className="font-medium text-zinc-950">
              {session?.customer_email ?? "paid@prompteer.dev"}
            </dd>
          </div>
        </dl>
      </div>

      <div className="rounded-lg border border-zinc-200 bg-white p-6 shadow-sm">
        <div className="flex items-start justify-between gap-4">
          <div>
            <h2 className="text-xl font-semibold text-zinc-950">
              Checkout session
            </h2>
            <p className="mt-2 text-sm leading-6 text-zinc-600">
              {session
                ? "A local Stripe-compatible session is ready."
                : "Create a session for the paid demo user."}
            </p>
          </div>
          <span className="rounded-md border border-zinc-200 px-2.5 py-1 text-xs font-medium capitalize text-zinc-700">
            {session?.payment_status ?? "unpaid"}
          </span>
        </div>

        <div className="mt-6 rounded-lg border border-zinc-200 bg-zinc-50 p-4">
          <dl className="grid gap-3 text-sm sm:grid-cols-2">
            <div>
              <dt className="text-zinc-500">Amount</dt>
              <dd className="mt-1 font-medium text-zinc-950">{price}</dd>
            </div>
            <div>
              <dt className="text-zinc-500">Status</dt>
              <dd className="mt-1 font-medium capitalize text-zinc-950">
                {session?.status ?? "not created"}
              </dd>
            </div>
            <div className="sm:col-span-2">
              <dt className="text-zinc-500">Session</dt>
              <dd className="mt-1 break-all font-mono text-xs text-zinc-700">
                {session?.id ?? "No checkout session yet"}
              </dd>
            </div>
          </dl>
        </div>

        <div className="mt-5 flex flex-wrap gap-3">
          <button
            className="inline-flex h-10 items-center gap-2 rounded-md bg-zinc-950 px-4 text-sm font-medium text-white transition hover:bg-zinc-800 disabled:cursor-not-allowed disabled:bg-zinc-400"
            disabled={!paymentsEnabled || isLoading}
            onClick={() => {
              void createCheckout();
            }}
            type="button"
          >
            {isLoading && step === "idle" ? (
              <Loader2 aria-hidden="true" className="h-4 w-4 animate-spin" />
            ) : (
              <CreditCard aria-hidden="true" className="h-4 w-4" />
            )}
            Start checkout
          </button>
          <button
            className="inline-flex h-10 items-center gap-2 rounded-md border border-zinc-300 px-4 text-sm font-medium text-zinc-900 transition hover:bg-zinc-50 disabled:cursor-not-allowed disabled:text-zinc-400"
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
          >
            {isLoading && step === "created" ? (
              <Loader2 aria-hidden="true" className="h-4 w-4 animate-spin" />
            ) : (
              <CheckCircle2 aria-hidden="true" className="h-4 w-4" />
            )}
            Complete mock checkout
          </button>
          <button
            className="inline-flex h-10 items-center gap-2 rounded-md border border-zinc-300 px-4 text-sm font-medium text-zinc-900 transition hover:bg-zinc-50"
            onClick={reset}
            type="button"
          >
            <RotateCcw aria-hidden="true" className="h-4 w-4" />
            Reset
          </button>
        </div>

        {!paymentsEnabled ? (
          <p className="mt-3 text-sm text-amber-700">
            Checkout is disabled by the environment feature flags.
          </p>
        ) : null}

        {error ? <p className="mt-4 text-sm text-red-600">{error}</p> : null}

        {step === "complete" ? (
          <div
            aria-live="polite"
            className="mt-6 rounded-lg border border-emerald-200 bg-emerald-50 p-4 text-sm leading-6 text-emerald-900"
          >
            Subscription active for {session?.customer_email}. The mock session
            completed with a Stripe-compatible{" "}
            <code>checkout.session.completed</code> event.
          </div>
        ) : null}
      </div>
    </section>
  );
}
