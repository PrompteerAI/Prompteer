// Legacy-preview labels and route helpers.
import type { components } from "@prompteer/shared-types";

export type Challenge = components["schemas"]["ChallengeRead"];
export type ChallengeTag = components["schemas"]["ChallengeTag"];
export type Level = components["schemas"]["ChallengeLevel"];
export type BoardFeed = components["schemas"]["BoardFeedRead"];
export type Post = components["schemas"]["PostRead"];
export type Share = components["schemas"]["ShareRead"];

export const categoryMeta: Record<
  ChallengeTag,
  {
    title: string;
    eyebrow: string;
    label: string;
    route: string;
    problemRoute: (challengeId: string) => string;
    accent: "blue" | "red" | "cyan";
  }
> = {
  ps: {
    title: "Algorithm",
    eyebrow: "Coding",
    label: "Algorithm",
    route: "/category/coding",
    problemRoute: (challengeId) => `/coding/problem/${challengeId}`,
    accent: "blue",
  },
  img: {
    title: "Image",
    eyebrow: "Image",
    label: "Image",
    route: "/category/image",
    problemRoute: (challengeId) => `/image/challenge/${challengeId}`,
    accent: "cyan",
  },
  video: {
    title: "Video",
    eyebrow: "Video",
    label: "Video",
    route: "/category/video",
    problemRoute: (challengeId) => `/video/challenge/${challengeId}`,
    accent: "red",
  },
};

export function levelLabel(level: Level): string {
  return {
    easy: "Easy",
    medium: "Medium",
    hard: "Hard",
  }[level];
}

export function levelClass(level: Level): string {
  return `difficulty-badge difficulty-${level}`;
}

export function challengeExcerpt(challenge: Challenge): string {
  return (
    challenge.content?.replace(/\s+/g, " ").trim() ??
    "Practice prompt design against this seeded Prompteer challenge."
  );
}

export function boardPostHref(postId: string): string {
  return `/board/post/${postId}`;
}

export function boardShareHref(shareId: string): string {
  return `/board/shared/${shareId}`;
}

export function formatBoardDate(createdAt: string): string {
  const date = new Date(createdAt);
  if (Number.isNaN(date.getTime())) {
    return "Unknown date";
  }

  return new Intl.DateTimeFormat("en", {
    month: "short",
    day: "numeric",
    year: "numeric",
  }).format(date);
}

export function findBoardPost(feed: BoardFeed, postId: string): Post | null {
  return feed.posts.find((post) => post.id === postId) ?? null;
}

export function findBoardShare(feed: BoardFeed, shareId: string): Share | null {
  return feed.shares.find((share) => share.id === shareId) ?? null;
}
