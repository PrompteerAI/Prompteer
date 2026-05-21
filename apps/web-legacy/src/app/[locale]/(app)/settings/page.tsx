// Legacy-preview account settings route.
import { ShieldCheck, UserRound } from "lucide-react";
import { getTranslations } from "next-intl/server";

import { readGatewaySession } from "@/lib/auth-gateway";
import { readFeatures } from "@/lib/data";

export const dynamic = "force-dynamic";

export default async function SettingsPage(): Promise<React.ReactElement> {
  const [t, commonT, session, features] = await Promise.all([
    getTranslations("legacy.settings"),
    getTranslations("legacy.common"),
    readGatewaySession(),
    readFeatures(),
  ]);

  return (
    <main className="legacy-page">
      <section className="legacy-section-banner compact">
        <h1>{t("title")}</h1>
        <p>{t("description")}</p>
      </section>
      <section className="legacy-settings-grid">
        <aside className="legacy-panel">
          <UserRound aria-hidden="true" color="#1971c2" size={32} />
          <h2 style={{ marginTop: 14 }}>{t("profile")}</h2>
          <p>{session?.user?.email ?? t("noActiveSession")}</p>
        </aside>
        <div className="legacy-panel">
          <div className="legacy-card-meta">
            <h2>{t("runtimeFeatures")}</h2>
            <ShieldCheck aria-hidden="true" color="#1971c2" size={20} />
          </div>
          <div className="legacy-card-meta">
            <span>{t("features.llm")}</span>
            <span className="legacy-pill">
              {features.llm ? commonT("enabled") : commonT("disabled")}
            </span>
          </div>
          <div className="legacy-card-meta">
            <span>{t("features.billing")}</span>
            <span className="legacy-pill">
              {features.payments ? commonT("enabled") : commonT("disabled")}
            </span>
          </div>
          <div className="legacy-card-meta">
            <span>{t("features.email")}</span>
            <span className="legacy-pill">
              {features.email ? commonT("enabled") : commonT("disabled")}
            </span>
          </div>
        </div>
      </section>
    </main>
  );
}
