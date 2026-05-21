// Legacy-preview route that opens a challenge from a board post.
import { getTranslations } from "next-intl/server";

import { Link } from "@/i18n/navigation";

type Props = {
  params: Promise<{ postId: string }>;
};

export default async function BoardPostProblemPage({
  params,
}: Props): Promise<React.ReactElement> {
  const { postId } = await params;
  const [t, commonT] = await Promise.all([
    getTranslations("legacy.board.problem"),
    getTranslations("legacy.common"),
  ]);

  return (
    <main className="legacy-page">
      <section className="legacy-board">
        <div className="legacy-section-banner compact">
          <h1>{t("title")}</h1>
          <p>{t("description", { postId })}</p>
        </div>
        <article className="legacy-panel">
          <p>{t("body")}</p>
          <Link
            className="legacy-secondary-button"
            href="/board"
            style={{ marginTop: 18 }}
          >
            {commonT("backBoard")}
          </Link>
        </article>
      </section>
    </main>
  );
}
