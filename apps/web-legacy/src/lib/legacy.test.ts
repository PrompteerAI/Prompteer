import { describe, expect, it } from "vitest";

import {
  boardPostHref,
  boardShareHref,
  categoryMeta,
  challengeExcerpt,
  challengeReferencePreview,
  findBoardPost,
  findBoardShare,
  formatBoardDate,
  isBrowserPreviewUrl,
  levelClass,
  levelLabel,
  type BoardFeed,
  type Challenge,
} from "./legacy";

const baseChallenge: Challenge = {
  id: "challenge-1",
  challenge_number: 1,
  tag: "ps",
  level: "medium",
  title: "Prompt repair",
  content: "  Repair a prompt with extra   whitespace. ",
  references: [],
};

const baseFeed: BoardFeed = {
  posts: [
    {
      id: "post-1",
      type: "question",
      tag: "ps",
      title: "How should I approach this?",
      content: "I need help with prompt structure.",
      author: {
        id: "user-1",
        display_name: "Ada",
        plan: "free",
      },
      challenge: {
        id: "challenge-1",
        challenge_number: 1,
        tag: "ps",
        level: "medium",
        title: "Prompt repair",
      },
      created_at: "2026-05-20T03:04:05Z",
    },
  ],
  shares: [
    {
      id: "share-1",
      prompt: "Explain the solution step by step.",
      is_public: true,
      author: {
        id: "user-2",
        display_name: "Grace",
        plan: "pro",
      },
      challenge: {
        id: "challenge-2",
        challenge_number: 2,
        tag: "img",
        level: "easy",
        title: "Image prompt",
      },
      created_at: "2026-05-21T03:04:05Z",
    },
  ],
  date_window: null,
};

describe("legacy helpers", () => {
  it("maps challenge levels to stable legacy labels and classes", () => {
    expect(levelLabel("easy")).toBe("Easy");
    expect(levelLabel("medium")).toBe("Medium");
    expect(levelLabel("hard")).toBe("Hard");
    expect(levelClass("hard")).toBe("difficulty-badge difficulty-hard");
  });

  it("keeps category routes compatible with the original frontend", () => {
    expect(categoryMeta.ps.route).toBe("/category/coding");
    expect(categoryMeta.img.problemRoute("abc")).toBe("/image/challenge/abc");
    expect(categoryMeta.video.problemRoute("abc")).toBe("/video/challenge/abc");
  });

  it("normalizes challenge excerpts for cards", () => {
    expect(challengeExcerpt(baseChallenge)).toBe(
      "Repair a prompt with extra whitespace.",
    );
    expect(challengeExcerpt({ ...baseChallenge, content: null })).toContain(
      "Practice prompt design",
    );
    expect(challengeExcerpt({ ...baseChallenge, content: "   " })).toContain(
      "Practice prompt design",
    );
  });

  it("omits reference preview metadata for coding challenges", () => {
    expect(challengeReferencePreview(baseChallenge)).toBeNull();
  });

  it("summarizes media references without treating storage paths as browser URLs", () => {
    const preview = challengeReferencePreview({
      ...baseChallenge,
      tag: "img",
      references: [
        {
          id: "reference-1",
          kind: "img",
          file_type: "image/png",
          file_path: "seed/references/product-hero.png",
        },
        {
          id: "reference-2",
          kind: "img",
          file_type: "image/jpeg",
          file_path: "https://cdn.example.com/secondary.jpg",
        },
      ],
    });

    expect(preview).toEqual({
      countLabel: "2 references",
      kind: "img",
      primaryReference: {
        filePath: "seed/references/product-hero.png",
        fileType: "image/png",
        kind: "img",
        previewUrl: null,
      },
      references: [
        {
          filePath: "seed/references/product-hero.png",
          fileType: "image/png",
          kind: "img",
          previewUrl: null,
        },
        {
          filePath: "https://cdn.example.com/secondary.jpg",
          fileType: "image/jpeg",
          kind: "img",
          previewUrl: "https://cdn.example.com/secondary.jpg",
        },
      ],
    });
  });

  it("normalizes blank media reference fields", () => {
    const preview = challengeReferencePreview({
      ...baseChallenge,
      tag: "video",
      references: [
        {
          id: "reference-1",
          kind: "video",
          file_type: "   ",
          file_path: "   ",
        },
      ],
    });

    expect(preview?.primaryReference).toEqual({
      filePath: "No reference file attached",
      fileType: "video reference",
      kind: "video",
      previewUrl: null,
    });
  });

  it("allows only directly renderable matching media preview URLs", () => {
    expect(
      isBrowserPreviewUrl("seed/references/launch-teaser.mp4", "video"),
    ).toBe(false);
    expect(isBrowserPreviewUrl("/references/launch-teaser.mp4", "video")).toBe(
      true,
    );
    expect(
      isBrowserPreviewUrl("https://cdn.example.com/reference.mp4", "video"),
    ).toBe(true);
    expect(isBrowserPreviewUrl("data:image/png;base64,abc", "img")).toBe(true);
    expect(isBrowserPreviewUrl("data:image/png,abc", "img")).toBe(true);
    expect(isBrowserPreviewUrl("data:text/plain;base64,abc", "img")).toBe(
      false,
    );
    expect(
      isBrowserPreviewUrl("https://cdn.example.com/reference.mp4", "img"),
    ).toBe(false);
    expect(
      isBrowserPreviewUrl("ftp://cdn.example.com/reference.mp4", "video"),
    ).toBe(false);
  });

  it("builds board read routes from backend ids", () => {
    expect(boardPostHref("post-1")).toBe("/board/post/post-1");
    expect(boardShareHref("share-1")).toBe("/board/shared/share-1");
  });

  it("formats board created dates and tolerates invalid input", () => {
    expect(formatBoardDate("2026-05-20T03:04:05Z")).toBe("May 20, 2026");
    expect(formatBoardDate("not-a-date")).toBe("Unknown date");
  });

  it("finds board feed records by backend id", () => {
    expect(findBoardPost(baseFeed, "post-1")?.title).toBe(
      "How should I approach this?",
    );
    expect(findBoardPost(baseFeed, "missing")).toBeNull();
    expect(findBoardShare(baseFeed, "share-1")?.challenge.title).toBe(
      "Image prompt",
    );
    expect(findBoardShare(baseFeed, "missing")).toBeNull();
  });
});
