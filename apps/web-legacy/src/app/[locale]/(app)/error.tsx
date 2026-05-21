// Legacy app route-group error boundary.
"use client";

import { useTranslations } from "next-intl";

export default function LegacyAppRouteGroupError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}): React.ReactElement {
  const t = useTranslations("errors");
  const showDetail = process.env.NODE_ENV !== "production";

  return (
    <main className="legacy-page">
      <section className="legacy-empty-state">
        <h1>{t("appTitle")}</h1>
        <p>{showDetail ? error.message : t("appDescription")}</p>
        {error.digest ? (
          <p>
            {t("supportId")}: {error.digest}
          </p>
        ) : null}
        <button className="legacy-primary-button" onClick={reset} type="button">
          {t("retry")}
        </button>
      </section>
    </main>
  );
}
