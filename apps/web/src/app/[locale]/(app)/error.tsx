// Protected app route-group error boundary.
"use client";

import * as Sentry from "@sentry/nextjs";
import { useMutation } from "@tanstack/react-query";
import { useTranslations } from "next-intl";
import { useEffect } from "react";

import { Button, Card } from "@/components/ui";
import { publicEnv } from "@/lib/env";

export default function AppRouteGroupError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}): React.ReactElement {
  const t = useTranslations("errors");
  const reportMutation = useMutation({
    mutationKey: ["client-error-report", "app", error.digest ?? error.message],
    mutationFn: () => reportError(error),
  });

  useEffect(() => {
    if (publicEnv.NEXT_PUBLIC_SENTRY_DSN) {
      Sentry.captureException(error);
    }
  }, [error]);

  return (
    <main className="min-h-[calc(100vh-73px)] bg-zinc-50 px-6 py-10 text-zinc-950">
      <Card className="mx-auto w-full max-w-md p-6">
        <h1 className="text-xl font-semibold text-zinc-950">{t("appTitle")}</h1>
        <p className="mt-2 text-sm leading-6 text-zinc-600">
          {t("appUnexpectedDescription")}
        </p>
        {error.digest ? (
          <p className="mt-3 break-all font-mono text-xs text-zinc-500">
            {t("supportId")}: {error.digest}
          </p>
        ) : null}
        <div className="mt-4 flex flex-wrap gap-3">
          <Button onClick={reset} type="button">
            {t("retry")}
          </Button>
          <Button
            disabled={reportMutation.isPending || reportMutation.isSuccess}
            onClick={() => {
              reportMutation.mutate();
            }}
            type="button"
            variant="outline"
          >
            {reportMutation.isSuccess ? t("reported") : t("report")}
          </Button>
        </div>
        {reportMutation.isError ? (
          <p className="mt-3 text-sm text-red-600" role="alert">
            {t("reportFailed")}
          </p>
        ) : null}
      </Card>
    </main>
  );
}

async function reportError(error: Error & { digest?: string }): Promise<void> {
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
  if (!response.ok) {
    throw new Error("Error report failed.");
  }
}
