import { ShieldCheck, UserRound } from "lucide-react";

import { readGatewaySession } from "@/lib/auth-gateway";
import { readFeatures } from "@/lib/data";

export const dynamic = "force-dynamic";

export default async function SettingsPage(): Promise<React.ReactElement> {
  const [session, features] = await Promise.all([
    readGatewaySession(),
    readFeatures(),
  ]);

  return (
    <main className="legacy-page">
      <section className="legacy-section-banner compact">
        <h1>Settings</h1>
        <p>
          Legacy sidebar settings layout backed by the rebuilt runtime config.
        </p>
      </section>
      <section className="legacy-settings-grid">
        <aside className="legacy-panel">
          <UserRound aria-hidden="true" color="#1971c2" size={32} />
          <h2 style={{ marginTop: 14 }}>Profile</h2>
          <p>{session?.user?.email ?? "No active session"}</p>
        </aside>
        <div className="legacy-panel">
          <div className="legacy-card-meta">
            <h2>Runtime features</h2>
            <ShieldCheck aria-hidden="true" color="#1971c2" size={20} />
          </div>
          <div className="legacy-card-meta">
            <span>LLM prompt runs</span>
            <span className="legacy-pill">
              {features.llm ? "enabled" : "disabled"}
            </span>
          </div>
          <div className="legacy-card-meta">
            <span>Billing checkout</span>
            <span className="legacy-pill">
              {features.payments ? "enabled" : "disabled"}
            </span>
          </div>
          <div className="legacy-card-meta">
            <span>Email capture</span>
            <span className="legacy-pill">
              {features.email ? "enabled" : "disabled"}
            </span>
          </div>
        </div>
      </section>
    </main>
  );
}
