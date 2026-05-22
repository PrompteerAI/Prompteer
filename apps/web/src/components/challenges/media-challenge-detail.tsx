// Read-only detail page for image and video prompt challenges.
import { ArrowLeft, FileImage, FileVideo } from "lucide-react";

import { ChallengeReferenceMetadata } from "./challenge-reference-metadata";
import { localizedPath } from "@/i18n/paths";
import {
  type ChallengeMediaChallenge,
  type ChallengeMediaKind,
  type ChallengeReferencePreviewLabels,
} from "@/lib/challenge-media";

type MediaChallengeDetailCopy = {
  backLabel: string;
  challengeNumberLabel: string;
  contentLabel: string;
  fallbackReferenceName: (number: number) => string;
  fileTypeLabel: string;
  kindLabel: string;
  levelLabel: string;
  noContent: string;
  noReferences: string;
  pathUnavailable: string;
  pathLabel: string;
  previewLabels: ChallengeReferencePreviewLabels;
  referenceLabel: string;
  referenceUnavailable: string;
  referencesTitle: string;
  unknownFileType: string;
};

type MediaChallengeDetailProps = {
  challenge: ChallengeMediaChallenge;
  copy: MediaChallengeDetailCopy;
  kind: ChallengeMediaKind;
  locale: string;
};

export function MediaChallengeDetail({
  challenge,
  copy,
  kind,
  locale,
}: MediaChallengeDetailProps): React.ReactElement {
  const Icon = kind === "img" ? FileImage : FileVideo;
  const listPath =
    kind === "img"
      ? localizedPath("/challenges/image", locale)
      : localizedPath("/challenges/video", locale);
  const content = challenge.content?.trim()
    ? challenge.content
    : copy.noContent;

  return (
    <article>
      <a
        className="inline-flex min-h-10 items-center gap-2 rounded-md text-sm font-medium text-zinc-700 transition hover:text-zinc-950 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-zinc-950"
        href={listPath}
      >
        <ArrowLeft aria-hidden="true" className="h-4 w-4" />
        {copy.backLabel}
      </a>
      <div className="mt-5 rounded-lg border border-zinc-200 bg-white p-6 shadow-sm">
        <div className="flex flex-col gap-5 lg:flex-row lg:items-start">
          <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-md bg-emerald-50 text-emerald-700">
            <Icon aria-label={copy.kindLabel} className="h-6 w-6" />
          </div>
          <div className="min-w-0 flex-1">
            <p className="text-sm font-semibold uppercase text-emerald-700">
              {copy.kindLabel} #{challenge.challenge_number}
            </p>
            <h1 className="mt-2 break-words text-3xl font-semibold text-zinc-950">
              {challenge.title}
            </h1>
            <dl className="mt-5 grid gap-3 text-sm sm:grid-cols-2 lg:grid-cols-3">
              <div className="rounded-md border border-zinc-200 px-3 py-2">
                <dt className="font-medium text-zinc-500">
                  {copy.challengeNumberLabel}
                </dt>
                <dd className="mt-1 text-zinc-950">
                  #{challenge.challenge_number}
                </dd>
              </div>
              <div className="rounded-md border border-zinc-200 px-3 py-2">
                <dt className="font-medium text-zinc-500">{copy.levelLabel}</dt>
                <dd className="mt-1 capitalize text-zinc-950">
                  {challenge.level}
                </dd>
              </div>
              <div className="rounded-md border border-zinc-200 px-3 py-2">
                <dt className="font-medium text-zinc-500">
                  {copy.referencesTitle}
                </dt>
                <dd className="mt-1 text-zinc-950">
                  {challenge.references.length}
                </dd>
              </div>
            </dl>
          </div>
        </div>
        <section className="mt-7">
          <h2 className="text-base font-semibold text-zinc-950">
            {copy.contentLabel}
          </h2>
          <p className="mt-3 max-w-3xl whitespace-pre-wrap text-sm leading-6 text-zinc-700">
            {content}
          </p>
        </section>
      </div>
      <section className="mt-6">
        <h2 className="text-xl font-semibold text-zinc-950">
          {copy.referencesTitle}
        </h2>
        {challenge.references.length > 0 ? (
          <div className="mt-4 grid gap-4 lg:grid-cols-2">
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
          <p className="mt-4 rounded-lg border border-dashed border-zinc-300 bg-white p-5 text-sm text-zinc-600">
            {copy.noReferences}
          </p>
        )}
      </section>
    </article>
  );
}
