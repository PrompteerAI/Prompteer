// Legacy auth route-group error boundary.
"use client";

import { useTranslations } from "next-intl";

export default function LegacyAuthRouteGroupError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}): React.ReactElement {
  const t = useTranslations("errors");
  const showDetail = process.env.NODE_ENV !== "production";

  return (
    <main className="legacy-auth-screen">
      <section className="legacy-auth-card">
        <h1>{t("authTitle")}</h1>
        <p>{showDetail ? error.message : t("authDescription")}</p>
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
