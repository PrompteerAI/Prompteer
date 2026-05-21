import { describe, expect, it } from "vitest";

import {
  categoryMeta,
  challengeExcerpt,
  levelClass,
  levelLabel,
  type Challenge,
} from "./legacy";

const baseChallenge: Challenge = {
  id: "challenge-1",
  challenge_number: 1,
  tag: "ps",
  level: "medium",
  title: "Prompt repair",
  content: "  Repair a prompt with extra   whitespace. ",
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
  });
});
