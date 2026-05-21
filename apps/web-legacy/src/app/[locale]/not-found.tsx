// Legacy-preview localized not-found route.
import { getTranslations } from "next-intl/server";

import { Link } from "@/i18n/navigation";

export default async function NotFoundPage(): Promise<React.ReactElement> {
  const t = await getTranslations("notFound");

  return (
    <main className="legacy-page">
      <section className="legacy-empty-state">
        <h1>{t("title")}</h1>
        <p>{t("description")}</p>
        <Link className="legacy-primary-button" href="/">
          {t("backHome")}
        </Link>
      </section>
    </main>
  );
}
