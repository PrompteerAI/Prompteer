import { MessageSquareText, Sparkles } from "lucide-react";

import { Link } from "@/i18n/navigation";
import { readBoard } from "@/lib/data";

export const dynamic = "force-dynamic";

export default async function BoardPage(): Promise<React.ReactElement> {
  const feed = await readBoard(12);
  const rows = [
    ...feed.posts.map((post) => ({
      id: post.id,
      title: post.title,
      category: post.tag.toUpperCase(),
      number: post.challenge?.challenge_number ?? "-",
      author: post.author.display_name,
      type: post.type,
      href: "/board",
    })),
    ...feed.shares.map((share) => ({
      id: share.id,
      title: share.challenge.title,
      category: share.challenge.tag.toUpperCase(),
      number: share.challenge.challenge_number,
      author: share.author.display_name,
      type: "share",
      href: "/board",
    })),
  ];

  return (
    <main className="legacy-page">
      <section className="legacy-board">
        <div className="legacy-section-banner compact">
          <h1>Board</h1>
          <p>
            Shared questions and prompt runs from the rebuilt community API.
          </p>
        </div>
        <div className="legacy-toolbar">
          <div className="legacy-filter-group">
            <button className="legacy-filter-button active" type="button">
              All
            </button>
            <button className="legacy-filter-button" type="button">
              Questions
            </button>
            <button className="legacy-filter-button" type="button">
              Shares
            </button>
          </div>
          <Link className="legacy-primary-button" href="/board/write">
            Write post
          </Link>
        </div>
        <div className="legacy-board-header">
          <span>Title</span>
          <span>Category</span>
          <span>Problem</span>
          <span>Author</span>
          <span>Type</span>
          <span>Date</span>
        </div>
        <div className="legacy-board-list">
          {rows.map((row) => (
            <Link
              className="legacy-board-row"
              href={row.href}
              key={`${row.type}-${row.id}`}
            >
              <span className="legacy-board-title">
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
              <span>{row.category}</span>
              <span>{row.number}</span>
              <span>{row.author}</span>
              <span>{row.type}</span>
              <span>Today</span>
            </Link>
          ))}
        </div>
      </section>
    </main>
  );
}
