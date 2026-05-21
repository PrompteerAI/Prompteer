import { ShieldCheck, Sparkles, UserRound } from "lucide-react";

import { Link } from "@/i18n/navigation";
import { authLoginUrl } from "@/lib/auth-gateway";

type Props = {
  params: Promise<{ locale: string }>;
};

export default async function LoginPage({
  params,
}: Props): Promise<React.ReactElement> {
  const { locale } = await params;
  const accounts = [
    {
      email: "admin@prompteer.dev",
      label: "Admin demo",
      Icon: ShieldCheck,
    },
    {
      email: "paid@prompteer.dev",
      label: "Paid demo",
      Icon: Sparkles,
    },
    {
      email: "free@prompteer.dev",
      label: "Free demo",
      Icon: UserRound,
    },
  ];

  return (
    <main className="legacy-auth-screen">
      <section className="legacy-auth-card">
        <h1>Sign in</h1>
        <p>
          The legacy preview uses the primary Prompteer web app as the Auth.js
          gateway. Demo buttons bridge through that app and return here.
        </p>
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
            Continue with primary login
          </a>
          <Link className="legacy-secondary-button" href="/">
            Back to home
          </Link>
        </div>
      </section>
    </main>
  );
}
