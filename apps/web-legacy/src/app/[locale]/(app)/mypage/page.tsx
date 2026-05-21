// Legacy-preview account summary route.
import { CreditCard, Mail, UserRound } from "lucide-react";
import { getTranslations } from "next-intl/server";

import { ChallengeCard } from "@/components/legacy/challenge-card";
import { Link } from "@/i18n/navigation";
import { readGatewaySession } from "@/lib/auth-gateway";
import { readChallenges, readIntegrations } from "@/lib/data";

export const dynamic = "force-dynamic";

export default async function MyPage(): Promise<React.ReactElement> {
  const [t, session, integrations, coding] = await Promise.all([
    getTranslations("legacy.myPage"),
    readGatewaySession(),
    readIntegrations(),
    readChallenges("ps"),
  ]);
  const user = session?.user;

  return (
    <main className="legacy-page">
      <section className="legacy-section-banner compact">
        <h1>{t("title")}</h1>
        <p>{t("description")}</p>
      </section>
      <section className="legacy-settings-grid">
        <aside className="legacy-panel">
          <UserRound aria-hidden="true" color="#1971c2" size={32} />
          <h2 style={{ marginTop: 14 }}>{user?.name ?? t("demoUser")}</h2>
          <p>{user?.email ?? t("signedOut")}</p>
          <Link
            className="legacy-primary-button"
            href="/billing"
            style={{ marginTop: 18 }}
          >
            <CreditCard aria-hidden="true" size={18} />
            {t("billing")}
          </Link>
        </aside>
        <div>
          <section className="legacy-panel">
            <h2>{t("integrationMode")}</h2>
            <p>{t("integrationDescription")}</p>
            <div className="legacy-card-meta">
              <span>{t("integrations.google")}</span>
              <span className="legacy-pill">{integrations.google_oauth}</span>
            </div>
            <div className="legacy-card-meta">
              <span>{t("integrations.llm")}</span>
              <span className="legacy-pill">{integrations.llm}</span>
            </div>
            <div className="legacy-card-meta">
              <span>{t("integrations.stripe")}</span>
              <span className="legacy-pill">{integrations.payments}</span>
            </div>
            <div className="legacy-card-meta">
              <span>{t("integrations.sendgrid")}</span>
              <span className="legacy-pill">{integrations.email}</span>
            </div>
          </section>
          <section className="legacy-panel" style={{ marginTop: 24 }}>
            <div className="legacy-card-meta">
              <h2>{t("recentPractice")}</h2>
              <Mail aria-hidden="true" color="#1971c2" size={20} />
            </div>
            <div className="legacy-challenge-grid" style={{ marginTop: 18 }}>
              {coding.slice(0, 3).map((challenge) => (
                <ChallengeCard challenge={challenge} key={challenge.id} />
              ))}
            </div>
          </section>
        </div>
      </section>
    </main>
  );
}
