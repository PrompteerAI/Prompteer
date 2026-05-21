// Legacy-preview board route showing shared prompt runs and discussion entries.
import { MessageSquareText, Sparkles } from "lucide-react";
import { getTranslations } from "next-intl/server";

import { Link } from "@/i18n/navigation";
import { readBoard } from "@/lib/data";
import { boardPostHref, boardShareHref, formatBoardDate } from "@/lib/legacy";

export const dynamic = "force-dynamic";

export default async function BoardPage(): Promise<React.ReactElement> {
  const [t, feed] = await Promise.all([
    getTranslations("legacy.board"),
    readBoard(12),
  ]);
  const rows = [
    ...feed.posts.map((post) => ({
      id: post.id,
      title: post.title,
      category: post.tag.toUpperCase(),
      number: post.challenge?.challenge_number ?? "-",
      author: post.author.display_name,
      type: post.type === "share" ? "share" : "question",
      href: boardPostHref(post.id),
      createdAt: post.created_at,
      sortAt: post.created_at,
    })),
    ...feed.shares.map((share) => ({
      id: share.id,
      title: share.challenge.title,
      category: share.challenge.tag.toUpperCase(),
      number: share.challenge.challenge_number,
      author: share.author.display_name,
      type: "share",
      href: boardShareHref(share.id),
      createdAt: share.created_at,
      sortAt: share.created_at,
    })),
  ].sort((a, b) => new Date(b.sortAt).getTime() - new Date(a.sortAt).getTime());

  return (
    <main className="legacy-page">
      <section className="legacy-board">
        <div className="legacy-section-banner compact">
          <h1>{t("title")}</h1>
          <p>{t("description")}</p>
        </div>
        <div className="legacy-toolbar">
          <div className="legacy-filter-group">
            <button className="legacy-filter-button active" type="button">
              {t("filters.all")}
            </button>
            <button className="legacy-filter-button" type="button">
              {t("filters.questions")}
            </button>
            <button className="legacy-filter-button" type="button">
              {t("filters.shares")}
            </button>
          </div>
          <Link className="legacy-primary-button" href="/board/write">
            {t("writePost")}
          </Link>
        </div>
        <div className="legacy-board-header">
          <span>{t("headers.title")}</span>
          <span>{t("headers.category")}</span>
          <span>{t("headers.problem")}</span>
          <span>{t("headers.author")}</span>
          <span>{t("headers.type")}</span>
          <span>{t("headers.date")}</span>
        </div>
        <div className="legacy-board-list">
          {rows.map((row) => (
            <Link
              className="legacy-board-row"
              href={row.href}
              key={`${row.type}-${row.id}`}
            >
              <span
                className="legacy-board-title"
                data-label={t("headers.title")}
              >
                {row.type === "share" ? (
                  <Sparkles
                    aria-hidden="true"
                    size={16}
                    style={{ marginRight: 7, verticalAlign: -2 }}
                  />
                ) : (
                  <MessageSquareText
                    aria-hidden="true"
                    size={16}
                    style={{ marginRight: 7, verticalAlign: -2 }}
                  />
                )}
                {row.title}
              </span>
              <span data-label={t("headers.category")}>{row.category}</span>
              <span data-label={t("headers.problem")}>{row.number}</span>
              <span data-label={t("headers.author")}>{row.author}</span>
              <span data-label={t("headers.type")}>
                {t(`types.${row.type}`)}
              </span>
              <span data-label={t("headers.date")}>
                {formatBoardDate(row.createdAt)}
              </span>
            </Link>
          ))}
        </div>
      </section>
    </main>
  );
}
