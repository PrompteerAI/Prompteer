// Global error boundary used when the app shell itself fails.
"use client";

// Root App Router error boundary. Locale-specific routes have their own
// fallback UI; this one catches failures above the locale segment.
import * as Sentry from "@sentry/nextjs";
import type { CSSProperties } from "react";
import { useEffect, useState } from "react";

import { publicEnv } from "@/lib/env";
import enMessages from "@/messages/en.json";

type ReportState = "idle" | "pending" | "success" | "error";

export default function GlobalError({
  error,
}: {
  error: Error & { digest?: string };
}): React.ReactElement {
  const [reportState, setReportState] = useState<ReportState>("idle");
  const t = enMessages.errors;

  useEffect(() => {
    if (publicEnv.NEXT_PUBLIC_SENTRY_DSN) {
      Sentry.captureException(error);
    }
  }, [error]);

  async function reportError(): Promise<void> {
    setReportState("pending");
    try {
      const response = await fetch("/api/errors", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({
          digest: error.digest,
          message: error.message,
          path: window.location.pathname,
          userAgent: window.navigator.userAgent,
        }),
      });
      setReportState(response.ok ? "success" : "error");
    } catch {
      setReportState("error");
    }
  }

  return (
    <html lang="en">
      <body>
        <main
          style={{
            alignItems: "center",
            background: "#fafafa",
            color: "#09090b",
            display: "grid",
            minHeight: "100vh",
            padding: 24,
          }}
        >
          <section
            style={{
              background: "#fff",
              border: "1px solid #e4e4e7",
              borderRadius: 8,
              boxShadow: "0 1px 2px rgba(0,0,0,0.04)",
              maxWidth: 448,
              padding: 24,
              width: "100%",
            }}
          >
            <h1 style={{ fontSize: 20, fontWeight: 700, margin: 0 }}>
              {t.rootTitle}
            </h1>
            <p style={{ color: "#52525b", lineHeight: 1.6, marginTop: 10 }}>
              {t.rootDescription}
            </p>
            {error.digest ? (
              <p
                style={{
                  color: "#71717a",
                  fontFamily: "monospace",
                  fontSize: 12,
                  overflowWrap: "anywhere",
                }}
              >
                {t.supportId}: {error.digest}
              </p>
            ) : null}
            <div style={{ display: "flex", flexWrap: "wrap", gap: 10 }}>
              <button
                onClick={() => {
                  window.location.reload();
                }}
                style={buttonStyle}
                type="button"
              >
                {t.retry}
              </button>
              <button
                disabled={
                  reportState === "pending" || reportState === "success"
                }
                onClick={() => {
                  void reportError();
                }}
                style={secondaryButtonStyle}
                type="button"
              >
                {reportState === "pending"
                  ? t.reporting
                  : reportState === "success"
                    ? t.reported
                    : t.report}
              </button>
            </div>
            {reportState === "error" ? (
              <p role="alert" style={{ color: "#b91c1c", marginBottom: 0 }}>
                {t.reportFailedDescription}
              </p>
            ) : null}
          </section>
        </main>
      </body>
    </html>
  );
}

const buttonStyle: CSSProperties = {
  background: "#18181b",
  border: 0,
  borderRadius: 8,
  color: "#fff",
  cursor: "pointer",
  fontWeight: 700,
  minHeight: 40,
  padding: "0 16px",
};

const secondaryButtonStyle: CSSProperties = {
  ...buttonStyle,
  background: "#fff",
  border: "1px solid #d4d4d8",
  color: "#18181b",
};
