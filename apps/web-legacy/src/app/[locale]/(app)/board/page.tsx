// Legacy-preview board route showing shared prompt runs and discussion entries.
import { getTranslations } from "next-intl/server";

import {
  BoardFeedBrowser,
  type LegacyBoardRow,
} from "@/components/legacy/board-feed-browser";
import { readBoard } from "@/lib/data";
import { boardPostHref, boardShareHref } from "@/lib/legacy";

export const dynamic = "force-dynamic";

export default async function BoardPage(): Promise<React.ReactElement> {
  const [t, feed] = await Promise.all([
    getTranslations("legacy.board"),
    readBoard(12),
  ]);
  const rows: LegacyBoardRow[] = [
    ...feed.posts.map((post) => ({
      id: post.id,
      title: post.title,
      category: post.tag.toUpperCase(),
      number: post.challenge?.challenge_number ?? "-",
      author: post.author.display_name,
      type: post.type === "share" ? ("share" as const) : ("question" as const),
      href: boardPostHref(post.id),
      createdAt: post.created_at,
    })),
    ...feed.shares.map((share) => ({
      id: share.id,
      title: share.challenge.title,
      category: share.challenge.tag.toUpperCase(),
      number: share.challenge.challenge_number,
      author: share.author.display_name,
      type: "share" as const,
      href: boardShareHref(share.id),
      createdAt: share.created_at,
    })),
  ].sort(
    (a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime(),
  );

  return (
    <main className="legacy-page">
      <section className="legacy-board">
        <div className="legacy-section-banner compact">
          <h1>{t("title")}</h1>
          <p>{t("description")}</p>
        </div>
        <BoardFeedBrowser
          labels={{
            all: t("filters.all"),
            author: t("headers.author"),
            category: t("headers.category"),
            date: t("headers.date"),
            noResults: t("noResults"),
            problem: t("headers.problem"),
            question: t("types.question"),
            questions: t("filters.questions"),
            share: t("types.share"),
            shares: t("filters.shares"),
            title: t("headers.title"),
            type: t("headers.type"),
            writePost: t("writePost"),
          }}
          rows={rows}
        />
      </section>
    </main>
  );
}
