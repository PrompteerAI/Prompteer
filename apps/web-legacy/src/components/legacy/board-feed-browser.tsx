// Client-side filtering table for the legacy-preview board feed.
"use client";

import { useMemo, useState } from "react";

import { MessageSquareText, Sparkles } from "lucide-react";

import { Link } from "@/i18n/navigation";
import { formatBoardDate } from "@/lib/legacy";

export type LegacyBoardRow = {
  author: string;
  category: string;
  createdAt: string;
  href: string;
  id: string;
  number: number | string;
  title: string;
  type: "question" | "share";
};

type BoardFilter = "all" | "question" | "share";

type BoardFeedBrowserProps = {
  labels: {
    date: string;
    all: string;
    author: string;
    category: string;
    noResults: string;
    problem: string;
    question: string;
    questions: string;
    share: string;
    shares: string;
    title: string;
    type: string;
    writePost: string;
  };
  rows: LegacyBoardRow[];
};

export function BoardFeedBrowser({
  labels,
  rows,
}: BoardFeedBrowserProps): React.ReactElement {
  const [filter, setFilter] = useState<BoardFilter>("all");
  const visibleRows = useMemo(
    () => (filter === "all" ? rows : rows.filter((row) => row.type === filter)),
    [filter, rows],
  );

  return (
    <>
      <div className="legacy-toolbar">
        <div className="legacy-filter-group">
          <button
            aria-pressed={filter === "all"}
            className={`legacy-filter-button${filter === "all" ? " active" : ""}`}
            onClick={() => {
              setFilter("all");
            }}
            type="button"
          >
            {labels.all}
          </button>
          <button
            aria-pressed={filter === "question"}
            className={`legacy-filter-button${filter === "question" ? " active" : ""}`}
            onClick={() => {
              setFilter("question");
            }}
            type="button"
          >
            {labels.questions}
          </button>
          <button
            aria-pressed={filter === "share"}
            className={`legacy-filter-button${filter === "share" ? " active" : ""}`}
            onClick={() => {
              setFilter("share");
            }}
            type="button"
          >
            {labels.shares}
          </button>
        </div>
        <Link className="legacy-primary-button" href="/board/write">
          {labels.writePost}
        </Link>
      </div>
      <div className="legacy-board-header">
        <span>{labels.title}</span>
        <span>{labels.category}</span>
        <span>{labels.problem}</span>
        <span>{labels.author}</span>
        <span>{labels.type}</span>
        <span>{labels.date}</span>
      </div>
      {visibleRows.length > 0 ? (
        <div className="legacy-board-list">
          {visibleRows.map((row) => (
            <Link
              className="legacy-board-row"
              href={row.href}
              key={`${row.type}-${row.id}`}
            >
              <span className="legacy-board-title" data-label={labels.title}>
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
              <span data-label={labels.category}>{row.category}</span>
              <span data-label={labels.problem}>{row.number}</span>
              <span data-label={labels.author}>{row.author}</span>
              <span data-label={labels.type}>
                {row.type === "share" ? labels.share : labels.question}
              </span>
              <span data-label={labels.date}>
                {formatBoardDate(row.createdAt)}
              </span>
            </Link>
          ))}
        </div>
      ) : (
        <p className="legacy-empty-list">{labels.noResults}</p>
      )}
    </>
  );
}
