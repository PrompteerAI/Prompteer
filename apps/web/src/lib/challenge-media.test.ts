// Unit tests for media challenge reference metadata fallbacks.
import { describe, expect, it } from "vitest";

import {
  challengeDetailPath,
  challengeMediaRouteSegment,
  isMediaChallenge,
  fileNameFromPath,
  referenceMetadata,
  type ChallengeMediaChallenge,
  type ChallengeReference,
} from "./challenge-media";

describe("challenge media helpers", () => {
  it("maps API tags to route segments", () => {
    expect(challengeMediaRouteSegment("img")).toBe("image");
    expect(challengeMediaRouteSegment("video")).toBe("video");
  });

  it("builds a media detail path from a media challenge", () => {
    const challenge: ChallengeMediaChallenge = {
      id: "challenge-123",
      challenge_number: 2,
      tag: "img",
      level: "medium",
      title: "Product hero image prompt",
      content: "Prompt content",
      references: [],
    };

    expect(challengeDetailPath(challenge)).toBe(
      "/challenges/image/challenge-123",
    );
  });

  it("recognizes image and video challenges only", () => {
    const imageChallenge: ChallengeMediaChallenge = {
      id: "challenge-123",
      challenge_number: 2,
      tag: "img",
      level: "medium",
      title: "Product hero image prompt",
      content: "Prompt content",
      references: [],
    };

    expect(isMediaChallenge(imageChallenge)).toBe(true);
    expect(isMediaChallenge(imageChallenge, "img")).toBe(true);
    expect(isMediaChallenge(imageChallenge, "video")).toBe(false);
    expect(isMediaChallenge({ ...imageChallenge, tag: "ps" })).toBe(false);
  });

  it("extracts readable file names from stored paths", () => {
    expect(fileNameFromPath("seed/references/product-hero.png")).toBe(
      "product-hero.png",
    );
    expect(fileNameFromPath("C:\\seed\\references\\launch-teaser.mp4")).toBe(
      "launch-teaser.mp4",
    );
    expect(fileNameFromPath("seed/reference.png?signature=local")).toBe(
      "reference.png",
    );
  });

  it("keeps stored paths as metadata and falls back when values are blank", () => {
    const reference: ChallengeReference = {
      id: "ref-1",
      kind: "video",
      file_path: "   ",
      file_type: "",
    };

    expect(
      referenceMetadata(reference, {
        fallbackFileName: "Reference 1",
        iconLabel: "Video",
        pathUnavailable: "Path unavailable",
        unknownFileType: "Unknown file type",
      }),
    ).toEqual({
      fileName: "Reference 1",
      filePath: "Path unavailable",
      fileType: "Unknown file type",
      iconLabel: "Video",
      kind: "video",
    });
  });
});
