// Footer mirrors the compact legacy app footer.
import { useTranslations } from "next-intl";

import { Link } from "@/i18n/navigation";

export function LegacyFooter(): React.ReactElement {
  const legacy = useTranslations("legacy");
  const t = useTranslations("legacy.footer");

  return (
    <footer className="legacy-footer">
      <div>
        <strong>{legacy("brand")}</strong>
        <p>{t("tagline")}</p>
      </div>
      <div className="legacy-footer-links">
        <a href="mailto:no-reply@prompteer.dev">{t("contact")}</a>
        <Link href="/settings">{t("settings")}</Link>
        <span>{t("copyright")}</span>
      </div>
    </footer>
  );
}
