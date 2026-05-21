// Legacy-preview signup route that guides users to mock login in dev.
import { getTranslations } from "next-intl/server";

import { Link } from "@/i18n/navigation";

export default async function SignupPage(): Promise<React.ReactElement> {
  const t = await getTranslations("legacy.auth.signup");

  return (
    <main className="legacy-auth-screen">
      <section
        className="legacy-auth-card"
        style={{ width: "min(762px, 100%)" }}
      >
        <h1>{t("title")}</h1>
        <p>{t("description")}</p>
        <div className="legacy-auth-actions">
          <Link className="legacy-primary-button" href="/login">
            {t("openDemoLogin")}
          </Link>
          <Link className="legacy-secondary-button" href="/">
            {t("backHome")}
          </Link>
        </div>
      </section>
    </main>
  );
}
