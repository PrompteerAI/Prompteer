// Header recreated from the original Prompteer frontend proportions.
import { LogIn, Settings, UserRound } from "lucide-react";

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
  const user = session?.user;

  return (
    <header className="legacy-header">
      <nav aria-label="Prompteer navigation" className="legacy-header-inner">
        <Link className="legacy-logo" href="/">
          PROMPTeer
        </Link>
        <LegacyNavLinks />
        <div className="legacy-account">
          {user ? (
            <>
              <Link className="legacy-icon-link" href="/mypage">
                <UserRound aria-hidden="true" size={16} />
                <span>{user.name ?? user.email ?? "My page"}</span>
              </Link>
              <Link className="legacy-icon-button" href="/settings">
                <Settings aria-hidden="true" size={16} />
                <span>Settings</span>
              </Link>
            </>
          ) : (
            <>
              <a
                className="legacy-icon-link"
                href={authLoginUrl(`/${locale}/login`)}
              >
                <LogIn aria-hidden="true" size={16} />
                <span>Login</span>
              </a>
              <Link className="legacy-primary-small" href="/login">
                Demo login
              </Link>
            </>
          )}
        </div>
      </nav>
    </header>
  );
}
