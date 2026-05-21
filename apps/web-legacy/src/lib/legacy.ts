// Legacy-preview labels and route helpers.
import type { components } from "@prompteer/shared-types";

export type Challenge = components["schemas"]["ChallengeRead"];
export type ChallengeTag = components["schemas"]["ChallengeTag"];
export type Level = components["schemas"]["ChallengeLevel"];
export type BoardFeed = components["schemas"]["BoardFeedRead"];
export type Post = components["schemas"]["PostRead"];
export type Share = components["schemas"]["ShareRead"];
export type ChallengeReference = Challenge["references"][number];

export interface ChallengeReferencePreviewItem {
  filePath: string;
  fileType: string;
  kind: "img" | "video";
  previewUrl: string | null;
}

export interface ChallengeReferencePreview {
  countLabel: string;
  kind: "img" | "video";
  primaryReference: ChallengeReferencePreviewItem | null;
  references: ChallengeReferencePreviewItem[];
}

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
  const excerpt = challenge.content?.replace(/\s+/g, " ").trim();
  return (
    excerpt || "Practice prompt design against this seeded Prompteer challenge."
  );
}

export function challengeReferencePreview(
  challenge: Challenge,
): ChallengeReferencePreview | null {
  if (challenge.tag === "ps") {
    return null;
  }

  const references = challenge.references.filter(
    (reference) => reference.kind === challenge.tag,
  );
  const kind = challenge.tag;
  const fallbackType = kind === "img" ? "image reference" : "video reference";
  const normalizedReferences = references.map((reference) =>
    normalizeReference(reference, fallbackType),
  );
  const primaryReference = normalizedReferences[0] ?? null;

  return {
    countLabel: `${references.length} ${references.length === 1 ? "reference" : "references"}`,
    kind,
    primaryReference,
    references: normalizedReferences,
  };
}

export function isBrowserPreviewUrl(
  filePath: string,
  kind?: "img" | "video",
): boolean {
  const trimmedPath = filePath.trim();
  if (!trimmedPath) {
    return false;
  }

  try {
    const url = new URL(trimmedPath);
    if (url.protocol === "blob:") {
      return true;
    }
    if (url.protocol === "data:") {
      return isSupportedDataMediaUrl(trimmedPath, kind);
    }
    if (url.protocol === "http:" || url.protocol === "https:") {
      return hasSupportedMediaExtension(url.pathname, kind);
    }
    return false;
  } catch {
    return trimmedPath.startsWith("/")
      ? hasSupportedMediaExtension(trimmedPath, kind)
      : false;
  }
}

function normalizeReference(
  reference: ChallengeReference,
  fallbackType: string,
): ChallengeReferencePreviewItem {
  const filePath = reference.file_path.trim();
  const fileType = reference.file_type.trim();

  return {
    filePath: filePath || "No reference file attached",
    fileType: fileType || fallbackType,
    kind: reference.kind,
    previewUrl: isBrowserPreviewUrl(filePath, reference.kind) ? filePath : null,
  };
}

function isSupportedDataMediaUrl(
  filePath: string,
  kind?: "img" | "video",
): boolean {
  const headerEnd = filePath.search(/[;,]/);
  const mediaType = filePath
    .slice(0, headerEnd === -1 ? filePath.length : headerEnd)
    .toLowerCase();
  if (kind === "img") {
    return mediaType.startsWith("data:image/");
  }
  if (kind === "video") {
    return mediaType.startsWith("data:video/");
  }
  return (
    mediaType.startsWith("data:image/") || mediaType.startsWith("data:video/")
  );
}

function hasSupportedMediaExtension(
  filePath: string,
  kind?: "img" | "video",
): boolean {
  const normalizedPath = filePath.split(/[?#]/, 1)[0]?.toLowerCase() ?? "";
  const imageMatch = /\.(apng|avif|bmp|gif|ico|jpe?g|png|svg|webp)$/.test(
    normalizedPath,
  );
  const videoMatch = /\.(m4v|mov|mp4|ogv|ogg|webm)$/.test(normalizedPath);

  if (kind === "img") {
    return imageMatch;
  }
  if (kind === "video") {
    return videoMatch;
  }
  return imageMatch || videoMatch;
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
