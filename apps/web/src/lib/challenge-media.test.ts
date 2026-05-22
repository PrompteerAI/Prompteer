// Unit tests for media challenge reference metadata fallbacks.
import { describe, expect, it } from "vitest";

import {
  challengeDetailPath,
  challengeMediaRouteSegment,
  isMediaChallenge,
  fileNameFromPath,
  referenceMetadata,
  referencePreview,
  type ChallengeMediaChallenge,
  type ChallengeReference,
  type ChallengeReferencePreviewLabels,
} from "./challenge-media";

const previewLabels: ChallengeReferencePreviewLabels = {
  generatedLocalImagePreview: "Generated local image preview",
  generatedLocalVideoPreview: "Generated local video preview",
  imageReference: "Image reference",
  launchTeaserSubtitle: "16:9 launch teaser storyboard",
  launchTeaserTitle: "Launch teaser",
  productHeroSubtitle: "Hero composition with product focus",
  productHeroTitle: "Product hero",
  referenceFile: "Reference file",
  videoReference: "Video reference",
};

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

    const metadata = referenceMetadata(reference, {
      fallbackFileName: "Reference 1",
      iconLabel: "Video",
      pathUnavailable: "Path unavailable",
      previewLabels,
      unknownFileType: "Unknown file type",
    });

    expect(metadata).toMatchObject({
      fileName: "Reference 1",
      filePath: "Path unavailable",
      fileType: "Unknown file type",
      iconLabel: "Video",
      kind: "video",
    });
    expect(metadata.preview).toMatchObject({
      subtitle: "Generated local video preview",
      title: "Reference 1",
      variant: "generic-video",
    });
  });

  it("uses curated deterministic previews for seeded media references", () => {
    const imageReference: ChallengeReference = {
      id: "ref-image",
      kind: "img",
      file_path: "seed/references/product-hero.png",
      file_type: "image/png",
    };
    const videoReference: ChallengeReference = {
      id: "ref-video",
      kind: "video",
      file_path: "seed/references/launch-teaser.mp4?signature=local",
      file_type: "video/mp4",
    };

    expect(
      referencePreview(imageReference, undefined, previewLabels),
    ).toMatchObject({
      eyebrow: "Image reference",
      subtitle: "Hero composition with product focus",
      title: "Product hero",
      variant: "product-hero",
    });
    expect(
      referencePreview(videoReference, undefined, previewLabels),
    ).toMatchObject({
      eyebrow: "Video reference",
      subtitle: "16:9 launch teaser storyboard",
      title: "Launch teaser",
      variant: "launch-teaser",
    });
    expect(
      referencePreview(imageReference, undefined, previewLabels).seed,
    ).toBe(referencePreview(imageReference, undefined, previewLabels).seed);
  });
});
