// Legacy-preview board composer placeholder route.
import { getTranslations } from "next-intl/server";

import { Link } from "@/i18n/navigation";

export default async function BoardWritePage(): Promise<React.ReactElement> {
  const [t, commonT] = await Promise.all([
    getTranslations("legacy.board.write"),
    getTranslations("legacy.common"),
  ]);

  return (
    <main className="legacy-page">
      <section className="legacy-board">
        <div className="legacy-section-banner compact">
          <h1>{t("title")}</h1>
          <p>{t("description")}</p>
        </div>
        <form className="legacy-panel">
          <label>
            {t("titleLabel")}
            <input className="legacy-search" readOnly value={t("titleValue")} />
          </label>
          <label style={{ display: "block", marginTop: 18 }}>
            {t("contentLabel")}
            <textarea
              className="legacy-prompt-area"
              readOnly
              value={t("contentValue")}
            />
          </label>
          <Link
            className="legacy-secondary-button"
            href="/board"
            style={{ marginTop: 18 }}
          >
            {commonT("backBoard")}
          </Link>
        </form>
      </section>
    </main>
  );
}
