// Legacy-preview login route with seed-user shortcuts.
import { ShieldCheck, Sparkles, UserRound } from "lucide-react";
import { getTranslations } from "next-intl/server";

import { Link } from "@/i18n/navigation";
import { authLoginUrl } from "@/lib/auth-gateway";

type Props = {
  params: Promise<{ locale: string }>;
};

export default async function LoginPage({
  params,
}: Props): Promise<React.ReactElement> {
  const { locale } = await params;
  const t = await getTranslations("legacy.auth.login");
  const accounts = [
    {
      email: "admin@prompteer.dev",
      label: t("adminDemo"),
      Icon: ShieldCheck,
    },
    {
      email: "paid@prompteer.dev",
      label: t("paidDemo"),
      Icon: Sparkles,
    },
    {
      email: "free@prompteer.dev",
      label: t("freeDemo"),
      Icon: UserRound,
    },
  ];

  return (
    <main className="legacy-auth-screen">
      <section className="legacy-auth-card">
        <h1>{t("title")}</h1>
        <p>{t("description")}</p>
        <div className="legacy-auth-actions">
          {accounts.map(({ email, label, Icon }) => (
            <a
              className="legacy-primary-button"
              href={`/dev/login-as/${encodeURIComponent(email)}?locale=${locale}`}
              key={email}
            >
              <Icon aria-hidden="true" size={18} />
              {label}
            </a>
          ))}
          <a
            className="legacy-secondary-button"
            href={authLoginUrl(`/${locale}/login`)}
          >
            {t("primaryLogin")}
          </a>
          <Link className="legacy-secondary-button" href="/">
            {t("backHome")}
          </Link>
        </div>
      </section>
    </main>
  );
}
