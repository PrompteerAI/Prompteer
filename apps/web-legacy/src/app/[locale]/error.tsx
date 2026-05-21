// Legacy-preview route-level error boundary.
"use client";

import { useTranslations } from "next-intl";
import { useState } from "react";

export default function ErrorPage({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}): React.ReactElement {
  const t = useTranslations("errors");
  const [reportStatus, setReportStatus] = useState<
    "idle" | "pending" | "reported" | "failed"
  >("idle");
  const showDetail = process.env.NODE_ENV !== "production";

  async function handleReport(): Promise<void> {
    setReportStatus("pending");
    const reported = await reportError(error);
    setReportStatus(reported ? "reported" : "failed");
  }

  return (
    <main className="legacy-page">
      <section className="legacy-empty-state">
        <h1>{t("title")}</h1>
        <p>{showDetail ? error.message : t("description")}</p>
        {error.digest ? (
          <p>{t("supportIdWithValue", { digest: error.digest })}</p>
        ) : null}
        <div className="legacy-auth-inline-actions">
          <button
            className="legacy-primary-button"
            onClick={reset}
            type="button"
          >
            {t("retry")}
          </button>
          <button
            className="legacy-secondary-button"
            disabled={reportStatus === "pending" || reportStatus === "reported"}
            onClick={() => void handleReport()}
            type="button"
          >
            {reportStatus === "reported"
              ? t("reported")
              : reportStatus === "failed"
                ? t("reportFailed")
                : t("report")}
          </button>
        </div>
      </section>
    </main>
  );
}

async function reportError(
  error: Error & { digest?: string },
): Promise<boolean> {
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
  return response.ok;
}
