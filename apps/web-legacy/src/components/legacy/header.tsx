// Header recreated from the original Prompteer frontend proportions.
import { LogIn, Settings, UserRound } from "lucide-react";
import { useTranslations } from "next-intl";

import { Link } from "@/i18n/navigation";
import { authLoginUrl, type GatewaySession } from "@/lib/auth-gateway";
import { LegacyNavLinks } from "./legacy-nav-links";

interface LegacyHeaderProps {
  locale: string;
  session: GatewaySession | null;
}

export function LegacyHeader({
  locale,
  session,
}: LegacyHeaderProps): React.ReactElement {
  const t = useTranslations("legacy.header");
  const brand = useTranslations("legacy");
  const user = session?.user;

  return (
    <header className="legacy-header">
      <nav aria-label={t("navigationLabel")} className="legacy-header-inner">
        <Link className="legacy-logo" href="/">
          {brand("brand")}
        </Link>
        <LegacyNavLinks />
        <div className="legacy-account">
          {user ? (
            <>
              <Link className="legacy-icon-link" href="/mypage">
                <UserRound aria-hidden="true" size={16} />
                <span>{user.name ?? user.email ?? t("myPageFallback")}</span>
              </Link>
              <Link className="legacy-icon-button" href="/settings">
                <Settings aria-hidden="true" size={16} />
                <span>{t("settings")}</span>
              </Link>
            </>
          ) : (
            <>
              <a
                className="legacy-icon-link"
                href={authLoginUrl(`/${locale}/login`)}
              >
                <LogIn aria-hidden="true" size={16} />
                <span>{t("login")}</span>
              </a>
              <Link className="legacy-primary-small" href="/login">
                {t("demoLogin")}
              </Link>
            </>
          )}
        </div>
      </nav>
    </header>
  );
}
