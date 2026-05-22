// Read-only list for image and video challenge types.
import { ArrowRight, FileImage, FileVideo } from "lucide-react";

import { ChallengeReferenceMetadata } from "./challenge-reference-metadata";
import { Link } from "@/i18n/navigation";
import {
  challengeDetailPath,
  type ChallengeMediaChallenge,
  type ChallengeMediaKind,
  type ChallengeReferencePreviewLabels,
} from "@/lib/challenge-media";

type MediaChallengeListCopy = {
  emptyTitle: string;
  emptyDescription: string;
  fallbackReferenceName: (number: number) => string;
  levelLabel: string;
  kindLabel: string;
  noContent: string;
  noReferences: string;
  openLabel: string;
  pathUnavailable: string;
  referenceLabel: string;
  referenceUnavailable: string;
  referencesLabel: string;
  fileTypeLabel: string;
  pathLabel: string;
  previewLabels: ChallengeReferencePreviewLabels;
  unknownFileType: string;
};

type MediaChallengeListProps = {
  challenges: ChallengeMediaChallenge[];
  copy: MediaChallengeListCopy;
  kind: ChallengeMediaKind;
};

export function MediaChallengeList({
  challenges,
  copy,
  kind,
}: MediaChallengeListProps): React.ReactElement {
  if (challenges.length === 0) {
    return (
      <section className="rounded-lg border border-dashed border-zinc-300 bg-white p-8">
        <h2 className="text-xl font-semibold text-zinc-950">
          {copy.emptyTitle}
        </h2>
        <p className="mt-3 max-w-2xl text-sm leading-6 text-zinc-600">
          {copy.emptyDescription}
        </p>
      </section>
    );
  }

  return (
    <section className="grid gap-4">
      {challenges.map((challenge) => (
        <MediaChallengeListItem
          challenge={challenge}
          copy={copy}
          key={challenge.id}
          kind={kind}
        />
      ))}
    </section>
  );
}

type MediaChallengeListItemProps = {
  challenge: ChallengeMediaChallenge;
  copy: MediaChallengeListCopy;
  kind: ChallengeMediaKind;
};

function MediaChallengeListItem({
  challenge,
  copy,
  kind,
}: MediaChallengeListItemProps): React.ReactElement {
  const Icon = kind === "img" ? FileImage : FileVideo;
  const content = challenge.content?.trim()
    ? challenge.content
    : copy.noContent;

  return (
    <article className="rounded-lg border border-zinc-200 bg-white p-5 shadow-sm">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div className="min-w-0">
          <p className="text-sm font-semibold uppercase text-emerald-700">
            {copy.kindLabel} #{challenge.challenge_number}
          </p>
          <h2 className="mt-2 break-words text-2xl font-semibold text-zinc-950">
            {challenge.title}
          </h2>
          <p className="mt-3 max-w-3xl text-sm leading-6 text-zinc-600">
            {content}
          </p>
          <dl className="mt-4 flex flex-wrap gap-3 text-sm">
            <div className="rounded-md border border-zinc-200 px-3 py-2">
              <dt className="font-medium text-zinc-500">{copy.levelLabel}</dt>
              <dd className="mt-1 capitalize text-zinc-950">
                {challenge.level}
              </dd>
            </div>
            <div className="rounded-md border border-zinc-200 px-3 py-2">
              <dt className="font-medium text-zinc-500">
                {copy.referencesLabel}
              </dt>
              <dd className="mt-1 text-zinc-950">
                {challenge.references.length}
              </dd>
            </div>
          </dl>
        </div>
        <Link
          aria-label={`${copy.openLabel}: ${challenge.title}`}
          className="inline-flex h-11 shrink-0 items-center justify-center gap-2 rounded-md bg-zinc-950 px-4 text-sm font-medium text-white transition hover:bg-zinc-800 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-zinc-950"
          href={challengeDetailPath(challenge)}
        >
          <Icon aria-hidden="true" className="h-4 w-4" />
          <span>{copy.openLabel}</span>
          <ArrowRight aria-hidden="true" className="h-4 w-4" />
        </Link>
      </div>
      {challenge.references.length > 0 ? (
        <div className="mt-5 grid gap-3 lg:grid-cols-2">
          {challenge.references.map((reference, index) => (
            <ChallengeReferenceMetadata
              fileTypeLabel={copy.fileTypeLabel}
              fallbackFileName={copy.fallbackReferenceName(index + 1)}
              iconLabel={copy.kindLabel}
              index={index}
              key={reference.id}
              pathUnavailableLabel={copy.pathUnavailable}
              pathLabel={copy.pathLabel}
              previewLabels={copy.previewLabels}
              reference={reference}
              referenceLabel={copy.referenceLabel}
              unknownFileTypeLabel={copy.unknownFileType}
              unavailableLabel={copy.referenceUnavailable}
            />
          ))}
        </div>
      ) : (
        <p className="mt-5 rounded-md bg-zinc-100 px-3 py-2 text-sm text-zinc-600">
          {copy.noReferences}
        </p>
      )}
    </article>
  );
}
