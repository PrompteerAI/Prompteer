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

  return {
    fileName,
    filePath: filePath || labels.pathUnavailable,
    fileType,
    iconLabel: labels.iconLabel,
    kind: reference.kind,
  };
}

export function fileNameFromPath(filePath: string): string {
  const normalizedPath = filePath.trim().replace(/\\/g, "/");
  const withoutQuery = normalizedPath.split(/[?#]/, 1)[0] ?? "";
  const segments = withoutQuery.split("/").filter(Boolean);
  return segments.at(-1) ?? "";
}
