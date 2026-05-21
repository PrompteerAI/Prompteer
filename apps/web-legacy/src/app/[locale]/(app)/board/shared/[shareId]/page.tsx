// Legacy-preview shared prompt run detail route.
import { getTranslations } from "next-intl/server";

import { Link } from "@/i18n/navigation";
import { ApiResponseError } from "@/lib/api-client";
import { readBoardShare, type Share } from "@/lib/data";
import { formatBoardDate } from "@/lib/legacy";

type Props = {
  params: Promise<{ shareId: string }>;
};

export default async function SharedPostPage({
  params,
}: Props): Promise<React.ReactElement> {
  const { shareId } = await params;
  const [t, commonT, share] = await Promise.all([
    getTranslations("legacy.board.detail"),
    getTranslations("legacy.common"),
    readShareDetail(shareId),
  ]);

  if (!share) {
    return (
      <main className="legacy-page">
        <section className="legacy-board">
          <div className="legacy-empty-state">
            <h1>{t("shareNotFoundTitle")}</h1>
            <p>{t("shareNotFoundDescription")}</p>
            <Link
              className="legacy-secondary-button"
              href="/board"
              style={{ marginTop: 18 }}
            >
              {commonT("backBoard")}
            </Link>
          </div>
        </section>
      </main>
    );
  }

  return (
    <main className="legacy-page">
      <section className="legacy-board">
        <div className="legacy-section-banner compact">
          <h1>{share.challenge.title}</h1>
          <p>
            {t("shareByline", {
              author: share.author.display_name,
              date: formatBoardDate(share.created_at),
            })}
          </p>
        </div>
        <article className="legacy-panel legacy-board-detail">
          <div
            className="legacy-detail-meta"
            aria-label={t("shareMetadataLabel")}
          >
            <span>
              {t("categoryMeta", {
                category: share.challenge.tag.toUpperCase(),
              })}
            </span>
            <span>
              {t("problemMeta", { number: share.challenge.challenge_number })}
            </span>
            <span>{t("authorPlanMeta", { plan: share.author.plan })}</span>
          </div>
          <h2>{t("promptHeading")}</h2>
          <p className="legacy-detail-body">
            {share.prompt ?? t("emptyPromptBody")}
          </p>
          <div className="legacy-detail-callout">
            <span>
              {t("problemLabel", {
                number: share.challenge.challenge_number,
              })}
            </span>
            <strong>{share.challenge.title}</strong>
            <p>
              {t("challengeSummary", {
                level: share.challenge.level,
                tag: share.challenge.tag.toUpperCase(),
              })}
            </p>
          </div>
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

async function readShareDetail(shareId: string): Promise<Share | null> {
  try {
    return await readBoardShare(shareId);
  } catch (error) {
    if (error instanceof ApiResponseError && error.response.status === 404) {
      return null;
    }
    throw error;
  }
}
