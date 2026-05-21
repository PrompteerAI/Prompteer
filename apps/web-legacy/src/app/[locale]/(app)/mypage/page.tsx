// Legacy-preview account summary route.
import { CreditCard, Mail, UserRound } from "lucide-react";

import { ChallengeCard } from "@/components/legacy/challenge-card";
import { Link } from "@/i18n/navigation";
import { readGatewaySession } from "@/lib/auth-gateway";
import { readChallenges, readIntegrations } from "@/lib/data";

export const dynamic = "force-dynamic";

export default async function MyPage(): Promise<React.ReactElement> {
  const [session, integrations, coding] = await Promise.all([
    readGatewaySession(),
    readIntegrations(),
    readChallenges("ps"),
  ]);
  const user = session?.user;

  return (
    <main className="legacy-page">
      <section className="legacy-section-banner compact">
        <h1>My page</h1>
        <p>Account, participation, and mock integration status.</p>
      </section>
      <section className="legacy-settings-grid">
        <aside className="legacy-panel">
          <UserRound aria-hidden="true" color="#1971c2" size={32} />
          <h2 style={{ marginTop: 14 }}>{user?.name ?? "Demo user"}</h2>
          <p>{user?.email ?? "Sign in through the primary web app."}</p>
          <Link
            className="legacy-primary-button"
            href="/billing"
            style={{ marginTop: 18 }}
          >
            <CreditCard aria-hidden="true" size={18} />
            Billing
          </Link>
        </aside>
        <div>
          <section className="legacy-panel">
            <h2>Integration mode</h2>
            <p>
              Blank credentials keep local development on deterministic mocks.
            </p>
            <div className="legacy-card-meta">
              <span>Google OAuth</span>
              <span className="legacy-pill">{integrations.google_oauth}</span>
            </div>
            <div className="legacy-card-meta">
              <span>LLM</span>
              <span className="legacy-pill">{integrations.llm}</span>
            </div>
            <div className="legacy-card-meta">
              <span>Stripe</span>
              <span className="legacy-pill">{integrations.payments}</span>
            </div>
            <div className="legacy-card-meta">
              <span>SendGrid</span>
              <span className="legacy-pill">{integrations.email}</span>
            </div>
          </section>
          <section className="legacy-panel" style={{ marginTop: 24 }}>
            <div className="legacy-card-meta">
              <h2>Recent algorithm practice</h2>
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
