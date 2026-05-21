// Legacy-preview board post detail route.
import { getTranslations } from "next-intl/server";

import { Link } from "@/i18n/navigation";
import { ApiResponseError } from "@/lib/api-client";
import { readBoardPost, type Post } from "@/lib/data";
import { formatBoardDate } from "@/lib/legacy";

type Props = {
  params: Promise<{ postId: string }>;
};

export default async function BoardPostPage({
  params,
}: Props): Promise<React.ReactElement> {
  const { postId } = await params;
  const [t, commonT, post] = await Promise.all([
    getTranslations("legacy.board.detail"),
    getTranslations("legacy.common"),
    readPostDetail(postId),
  ]);

  if (!post) {
    return (
      <main className="legacy-page">
        <section className="legacy-board">
          <div className="legacy-empty-state">
            <h1>{t("postNotFoundTitle")}</h1>
            <p>{t("postNotFoundDescription")}</p>
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
          <h1>{post.title}</h1>
          <p>
            {t("postByline", {
              author: post.author.display_name,
              date: formatBoardDate(post.created_at),
              type:
                post.type === "share"
                  ? t("postTypes.share")
                  : t("postTypes.question"),
            })}
          </p>
        </div>
        <article className="legacy-panel legacy-board-detail">
          <div
            className="legacy-detail-meta"
            aria-label={t("postMetadataLabel")}
          >
            <span>
              {t("categoryMeta", { category: post.tag.toUpperCase() })}
            </span>
            <span>
              {t("typeMeta", {
                type:
                  post.type === "share"
                    ? t("postTypes.share")
                    : t("postTypes.question"),
              })}
            </span>
            <span>{t("authorPlanMeta", { plan: post.author.plan })}</span>
          </div>
          <h2>{t("postHeading")}</h2>
          <p className="legacy-detail-body">
            {post.content ?? t("emptyPostBody")}
          </p>
          {post.challenge ? (
            <div className="legacy-detail-callout">
              <span>
                {t("problemLabel", {
                  number: post.challenge.challenge_number,
                })}
              </span>
              <strong>{post.challenge.title}</strong>
              <p>
                {t("challengeSummary", {
                  level: post.challenge.level,
                  tag: post.challenge.tag.toUpperCase(),
                })}
              </p>
            </div>
          ) : null}
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

async function readPostDetail(postId: string): Promise<Post | null> {
  try {
    return await readBoardPost(postId);
  } catch (error) {
    if (error instanceof ApiResponseError && error.response.status === 404) {
      return null;
    }
    throw error;
  }
}
