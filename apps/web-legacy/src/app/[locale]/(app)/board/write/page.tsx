// Legacy-preview board composer placeholder route.
import { getTranslations } from "next-intl/server";

import { BoardWriteForm } from "@/components/legacy/board-write-form";

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
        <BoardWriteForm
          labels={{
            backBoard: commonT("backBoard"),
            contentLabel: t("contentLabel"),
            contentValue: t("contentValue"),
            draftSaved: t("draftSaved"),
            previewTitle: t("previewTitle"),
            reset: t("reset"),
            submit: t("submit"),
            titleLabel: t("titleLabel"),
            titleValue: t("titleValue"),
            typeLabel: t("typeLabel"),
            typeQuestion: t("typeQuestion"),
            typeShare: t("typeShare"),
            validationError: t("validationError"),
          }}
        />
      </section>
    </main>
  );
}
