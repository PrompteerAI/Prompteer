"use client";

// Localized route-level error boundary for recoverable rendering failures.
import * as Sentry from "@sentry/nextjs";
import { useTranslations } from "next-intl";
import { useEffect, useState } from "react";

import { publicEnv } from "@/lib/env";

export default function ErrorPage({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}): React.ReactElement {
  const t = useTranslations("errors");
  const [reportState, setReportState] = useState<"idle" | "sending" | "sent">(
    "idle",
  );

  useEffect(() => {
    if (publicEnv.NEXT_PUBLIC_SENTRY_DSN) {
      Sentry.captureException(error);
    }
  }, [error]);

  async function reportError(): Promise<void> {
    if (reportState !== "idle") {
      return;
    }
    setReportState("sending");
    try {
      const response = await fetch("/api/errors", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({
          message: error.message,
          digest: error.digest,
          path: window.location.pathname,
          userAgent: window.navigator.userAgent,
        }),
      });
      setReportState(response.ok ? "sent" : "idle");
    } catch {
      setReportState("idle");
    }
  }

  return (
    <main className="grid min-h-screen place-items-center bg-zinc-50 px-6">
      <div className="w-full max-w-md rounded-lg border border-zinc-200 bg-white p-6">
        <h1 className="text-xl font-semibold text-zinc-950">{t("title")}</h1>
        <p className="mt-2 text-sm text-zinc-600">{error.message}</p>
        <div className="mt-4 flex flex-wrap gap-3">
          <button
            className="rounded-md bg-zinc-950 px-4 py-2 text-sm text-white"
            onClick={reset}
          >
            {t("retry")}
          </button>
          <button
            className="rounded-md border border-zinc-300 px-4 py-2 text-sm text-zinc-900 disabled:cursor-not-allowed disabled:text-zinc-500"
            disabled={reportState !== "idle"}
            onClick={() => {
              void reportError();
            }}
          >
            {reportState === "sent" ? t("reported") : t("report")}
          </button>
        </div>
      </div>
    </main>
  );
}
