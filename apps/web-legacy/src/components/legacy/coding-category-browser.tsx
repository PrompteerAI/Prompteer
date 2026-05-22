// Client-side search and sort controls for legacy coding challenges.
"use client";

import { useMemo, useState } from "react";

import { ChallengeCard } from "@/components/legacy/challenge-card";
import type { Challenge } from "@/lib/data";

type SortMode = "difficulty" | "recent";

type CodingCategoryBrowserProps = {
  challenges: Challenge[];
  labels: {
    difficulty: string;
    noResults: string;
    recent: string;
    searchPlaceholder: string;
  };
};

const DIFFICULTY_RANK: Record<Challenge["level"], number> = {
  easy: 1,
  medium: 2,
  hard: 3,
};

export function CodingCategoryBrowser({
  challenges,
  labels,
}: CodingCategoryBrowserProps): React.ReactElement {
  const [query, setQuery] = useState("");
  const [sortMode, setSortMode] = useState<SortMode>("difficulty");

  const visibleChallenges = useMemo(() => {
    const normalizedQuery = query.trim().toLowerCase();
    const filtered = normalizedQuery
      ? challenges.filter((challenge) =>
          [
            challenge.title,
            challenge.content ?? "",
            challenge.level,
            String(challenge.challenge_number),
          ].some((value) => value.toLowerCase().includes(normalizedQuery)),
        )
      : challenges;

    return [...filtered].sort((a, b) => {
      if (sortMode === "recent") {
        return b.challenge_number - a.challenge_number;
      }
      return (
        DIFFICULTY_RANK[a.level] - DIFFICULTY_RANK[b.level] ||
        a.challenge_number - b.challenge_number
      );
    });
  }, [challenges, query, sortMode]);

  return (
    <>
      <div className="legacy-toolbar">
        <input
          aria-label={labels.searchPlaceholder}
          className="legacy-search"
          onChange={(event) => {
            setQuery(event.target.value);
          }}
          placeholder={labels.searchPlaceholder}
          type="search"
          value={query}
        />
        <div className="legacy-filter-group">
          <button
            aria-pressed={sortMode === "difficulty"}
            className={`legacy-filter-button${sortMode === "difficulty" ? " active" : ""}`}
            onClick={() => {
              setSortMode("difficulty");
            }}
            type="button"
          >
            {labels.difficulty}
          </button>
          <button
            aria-pressed={sortMode === "recent"}
            className={`legacy-filter-button${sortMode === "recent" ? " active" : ""}`}
            onClick={() => {
              setSortMode("recent");
            }}
            type="button"
          >
            {labels.recent}
          </button>
        </div>
      </div>
      {visibleChallenges.length > 0 ? (
        <section className="legacy-challenge-grid">
          {visibleChallenges.map((challenge) => (
            <ChallengeCard challenge={challenge} key={challenge.id} />
          ))}
        </section>
      ) : (
        <p className="legacy-empty-list">{labels.noResults}</p>
      )}
    </>
  );
}
