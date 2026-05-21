// Helpers for presenting challenge reference metadata without assuming files
// are publicly served by the web app.
import type { components } from "@prompteer/shared-types";

export type Challenge = components["schemas"]["ChallengeRead"];
export type ChallengeMediaKind = Extract<Challenge["tag"], "img" | "video">;
export type ChallengeMediaChallenge = Challenge & { tag: ChallengeMediaKind };
export type ChallengeReference = Challenge["references"][number];

export type ChallengeReferenceMetadata = {
  fileName: string;
  filePath: string;
  fileType: string;
  iconLabel: string;
  kind: ChallengeReference["kind"];
  preview: ChallengeReferencePreview;
};

export type ChallengeReferencePreview = {
  accentColor: string;
  background: string;
  eyebrow: string;
  seed: number;
  subtitle: string;
  title: string;
  variant: "generic-image" | "generic-video" | "launch-teaser" | "product-hero";
};

const PREVIEW_PALETTES = [
  {
    accentColor: "#059669",
    background:
      "radial-gradient(circle at 18% 18%, rgba(16, 185, 129, 0.32), transparent 30%), linear-gradient(135deg, #f8fafc 0%, #dbeafe 48%, #ecfdf5 100%)",
  },
  {
    accentColor: "#2563eb",
    background:
      "radial-gradient(circle at 82% 20%, rgba(37, 99, 235, 0.3), transparent 28%), linear-gradient(135deg, #fff7ed 0%, #e0f2fe 52%, #f8fafc 100%)",
  },
  {
    accentColor: "#c2410c",
    background:
      "radial-gradient(circle at 24% 76%, rgba(249, 115, 22, 0.24), transparent 30%), linear-gradient(135deg, #f8fafc 0%, #fee2e2 48%, #fefce8 100%)",
  },
] as const;

const SEEDED_PREVIEWS: Record<
  string,
  Pick<
    ChallengeReferencePreview,
    "accentColor" | "background" | "eyebrow" | "subtitle" | "title" | "variant"
  >
> = {
  "seed/references/launch-teaser.mp4": {
    accentColor: "#2563eb",
    background:
      "radial-gradient(circle at 74% 18%, rgba(96, 165, 250, 0.38), transparent 24%), linear-gradient(135deg, #111827 0%, #1d4ed8 48%, #f97316 100%)",
    eyebrow: "Video reference",
    subtitle: "16:9 launch teaser storyboard",
    title: "Launch teaser",
    variant: "launch-teaser",
  },
  "seed/references/product-hero.png": {
    accentColor: "#059669",
    background:
      "radial-gradient(circle at 20% 22%, rgba(16, 185, 129, 0.32), transparent 24%), linear-gradient(135deg, #f8fafc 0%, #d1fae5 45%, #bfdbfe 100%)",
    eyebrow: "Image reference",
    subtitle: "Hero composition with product focus",
    title: "Product hero",
    variant: "product-hero",
  },
};

export function challengeMediaRouteSegment(
  kind: ChallengeMediaKind,
): "image" | "video" {
  return kind === "img" ? "image" : "video";
}

export function challengeMediaTagFromRoute(
  segment: "image" | "video",
): ChallengeMediaKind {
  return segment === "image" ? "img" : "video";
}

export function isMediaChallenge(
  challenge: Challenge,
  kind?: ChallengeMediaKind,
): challenge is ChallengeMediaChallenge {
  const hasMediaTag = challenge.tag === "img" || challenge.tag === "video";
  return hasMediaTag && (kind === undefined || challenge.tag === kind);
}

export function challengeDetailPath(
  challenge: ChallengeMediaChallenge,
): string {
  const segment = challengeMediaRouteSegment(challenge.tag);
  return `/challenges/${segment}/${challenge.id}`;
}

export function referenceMetadata(
  reference: ChallengeReference,
  labels: {
    fallbackFileName: string;
    iconLabel: string;
    pathUnavailable: string;
    unknownFileType: string;
  },
): ChallengeReferenceMetadata {
  const filePath = reference.file_path.trim();
  const fileName = fileNameFromPath(filePath) || labels.fallbackFileName;
  const fileType = reference.file_type.trim() || labels.unknownFileType;
  const preview = referencePreview(reference, fileName);

  return {
    fileName,
    filePath: filePath || labels.pathUnavailable,
    fileType,
    iconLabel: labels.iconLabel,
    kind: reference.kind,
    preview,
  };
}

export function fileNameFromPath(filePath: string): string {
  const normalizedPath = filePath.trim().replace(/\\/g, "/");
  const withoutQuery = normalizedPath.split(/[?#]/, 1)[0] ?? "";
  const segments = withoutQuery.split("/").filter(Boolean);
  return segments.at(-1) ?? "";
}

export function referencePreview(
  reference: ChallengeReference,
  fallbackTitle?: string,
): ChallengeReferencePreview {
  const normalizedPath = normalizeStoredPath(reference.file_path);
  const seededPreview = SEEDED_PREVIEWS[normalizedPath];
  const seed = hashReference(`${normalizedPath}:${reference.kind}`);

  if (seededPreview) {
    return {
      ...seededPreview,
      seed,
    };
  }

  const palette =
    PREVIEW_PALETTES[seed % PREVIEW_PALETTES.length] ?? PREVIEW_PALETTES[0];
  const isVideo = reference.kind === "video";
  const title =
    fallbackTitle || fileNameFromPath(reference.file_path) || "Reference file";

  return {
    accentColor: palette.accentColor,
    background: palette.background,
    eyebrow: isVideo ? "Video reference" : "Image reference",
    seed,
    subtitle: isVideo
      ? "Generated local video preview"
      : "Generated local image preview",
    title,
    variant: isVideo ? "generic-video" : "generic-image",
  };
}

function normalizeStoredPath(filePath: string): string {
  return (
    filePath.trim().replace(/\\/g, "/").split(/[?#]/, 1)[0]?.toLowerCase() ?? ""
  );
}

function hashReference(value: string): number {
  let hash = 0;

  for (const character of value) {
    hash = (hash * 31 + character.charCodeAt(0)) >>> 0;
  }

  return hash;
}
