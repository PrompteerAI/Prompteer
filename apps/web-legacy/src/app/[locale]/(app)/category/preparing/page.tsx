// Legacy-preview route for categories that are not yet available.
import { Clock3 } from "lucide-react";
import { getTranslations } from "next-intl/server";

import { Link } from "@/i18n/navigation";

export default async function PreparingPage(): Promise<React.ReactElement> {
  const [t, commonT] = await Promise.all([
    getTranslations("legacy.categories.preparing"),
    getTranslations("legacy.common"),
  ]);

  return (
    <main className="legacy-page">
      <section className="legacy-empty-state">
        <Clock3 aria-hidden="true" color="#1971c2" size={80} />
        <h1>{t("title")}</h1>
        <p>{t("description")}</p>
        <Link className="legacy-primary-button" href="/">
          {commonT("backHome")}
        </Link>
      </section>
    </main>
  );
}
