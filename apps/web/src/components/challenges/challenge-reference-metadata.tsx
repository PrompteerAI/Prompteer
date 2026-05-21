// Read-only metadata cards for media challenge references. Previews are local
// deterministic compositions, not fetched media files.
import type { CSSProperties } from "react";

import { FileImage, FileVideo, Play, Sparkles } from "lucide-react";

import {
  referenceMetadata,
  type ChallengeReferenceMetadata as ChallengeReferenceMetadataValue,
  type ChallengeReference,
} from "@/lib/challenge-media";

type ChallengeReferenceMetadataProps = {
  unavailableLabel: string;
  fallbackFileName: string;
  fileTypeLabel: string;
  iconLabel: string;
  pathUnavailableLabel: string;
  pathLabel: string;
  reference: ChallengeReference;
  referenceLabel: string;
  unknownFileTypeLabel: string;
  index: number;
};

export function ChallengeReferenceMetadata({
  unavailableLabel,
  fallbackFileName,
  fileTypeLabel,
  iconLabel,
  index,
  pathUnavailableLabel,
  pathLabel,
  reference,
  referenceLabel,
  unknownFileTypeLabel,
}: ChallengeReferenceMetadataProps): React.ReactElement {
  const metadata = referenceMetadata(reference, {
    fallbackFileName,
    iconLabel,
    pathUnavailable: pathUnavailableLabel,
    unknownFileType: unknownFileTypeLabel,
  });
  const Icon = metadata.kind === "img" ? FileImage : FileVideo;

  return (
    <article className="overflow-hidden rounded-lg border border-zinc-200 bg-white shadow-sm">
      <ReferencePreviewPanel
        metadata={metadata}
        statusLabel={unavailableLabel}
      />
      <div className="p-4">
        <div className="flex items-start gap-3">
          <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-md bg-emerald-50 text-emerald-700">
            <Icon aria-label={metadata.iconLabel} className="h-5 w-5" />
          </div>
          <div className="min-w-0">
            <p className="text-xs font-semibold uppercase text-zinc-500">
              {referenceLabel} {index + 1}
            </p>
            <h3 className="mt-1 break-words text-base font-semibold text-zinc-950">
              {metadata.fileName}
            </h3>
            <p className="mt-2 text-sm leading-6 text-zinc-600">
              {metadata.preview.subtitle}
            </p>
          </div>
        </div>
        <dl className="mt-4 grid gap-3 text-sm sm:grid-cols-2">
          <div>
            <dt className="font-medium text-zinc-500">{fileTypeLabel}</dt>
            <dd className="mt-1 break-words text-zinc-900">
              {metadata.fileType}
            </dd>
          </div>
          <div>
            <dt className="sr-only">{pathLabel}</dt>
            <dd>
              <details className="group">
                <summary className="cursor-pointer list-none font-medium text-zinc-500 transition hover:text-zinc-800 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-zinc-950">
                  {pathLabel}
                </summary>
                <div className="mt-1 break-words rounded-md bg-zinc-100 p-2 font-mono text-xs text-zinc-700">
                  {metadata.filePath}
                </div>
              </details>
            </dd>
          </div>
        </dl>
      </div>
    </article>
  );
}

function ReferencePreviewPanel({
  metadata,
  statusLabel,
}: {
  metadata: ChallengeReferenceMetadataValue;
  statusLabel: string;
}): React.ReactElement {
  const previewStyle = {
    "--reference-accent": metadata.preview.accentColor,
    background: metadata.preview.background,
  } as CSSProperties;
  const isVideo = metadata.kind === "video";

  return (
    <div
      aria-label={`${statusLabel}: ${metadata.preview.title}`}
      className="relative aspect-video overflow-hidden border-b border-zinc-200"
      role="img"
      style={previewStyle}
    >
      <div className="absolute inset-0 bg-[linear-gradient(120deg,rgba(255,255,255,0.7),transparent_42%,rgba(255,255,255,0.28))]" />
      <div className="absolute left-4 top-4 inline-flex items-center gap-2 rounded-full bg-white/90 px-3 py-1 text-xs font-semibold text-zinc-800 shadow-sm ring-1 ring-black/5 backdrop-blur">
        {isVideo ? (
          <Play aria-hidden="true" className="h-3.5 w-3.5" />
        ) : (
          <Sparkles aria-hidden="true" className="h-3.5 w-3.5" />
        )}
        <span>{statusLabel}</span>
      </div>
      {metadata.preview.variant === "product-hero" ? (
        <ProductHeroPreview metadata={metadata} />
      ) : metadata.preview.variant === "launch-teaser" ? (
        <LaunchTeaserPreview metadata={metadata} />
      ) : (
        <GenericReferencePreview metadata={metadata} />
      )}
    </div>
  );
}

function ProductHeroPreview({
  metadata,
}: {
  metadata: ChallengeReferenceMetadataValue;
}): React.ReactElement {
  return (
    <div className="absolute inset-x-5 bottom-5 top-14 grid grid-cols-[1fr_1.05fr] gap-4">
      <div className="flex min-w-0 flex-col justify-end rounded-md bg-white/80 p-4 shadow-sm ring-1 ring-black/5 backdrop-blur">
        <p className="text-xs font-semibold uppercase text-zinc-500">
          {metadata.preview.eyebrow}
        </p>
        <p className="mt-1 text-xl font-semibold text-zinc-950">
          {metadata.preview.title}
        </p>
        <div className="mt-4 h-2 w-20 rounded-full bg-[var(--reference-accent)]" />
        <div className="mt-3 h-2 w-28 rounded-full bg-zinc-200" />
      </div>
      <div className="relative overflow-hidden rounded-md bg-white/75 shadow-sm ring-1 ring-black/5 backdrop-blur">
        <div className="absolute left-1/2 top-1/2 h-24 w-24 -translate-x-1/2 -translate-y-1/2 rounded-2xl bg-[var(--reference-accent)] shadow-xl" />
        <div className="absolute left-1/2 top-1/2 h-16 w-16 -translate-x-[38%] -translate-y-[64%] rounded-full bg-white/70" />
        <div className="absolute bottom-5 left-5 right-5 h-3 rounded-full bg-zinc-950/10" />
      </div>
    </div>
  );
}

function LaunchTeaserPreview({
  metadata,
}: {
  metadata: ChallengeReferenceMetadataValue;
}): React.ReactElement {
  return (
    <div className="absolute inset-x-5 bottom-5 top-14 overflow-hidden rounded-md bg-zinc-950/80 p-4 text-white shadow-sm ring-1 ring-white/20">
      <div className="flex h-full flex-col justify-between">
        <div>
          <p className="text-xs font-semibold uppercase text-white/70">
            {metadata.preview.eyebrow}
          </p>
          <p className="mt-1 max-w-48 text-2xl font-semibold leading-tight">
            {metadata.preview.title}
          </p>
        </div>
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-full bg-white text-zinc-950">
            <Play aria-hidden="true" className="h-4 w-4 fill-current" />
          </div>
          <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-white/20">
            <div className="h-full w-2/3 rounded-full bg-white" />
          </div>
          <span className="text-xs font-medium text-white/75">00:12</span>
        </div>
      </div>
      <div className="absolute right-7 top-8 h-20 w-20 rounded-full bg-orange-300/80 blur-sm" />
      <div className="absolute bottom-14 right-14 h-24 w-16 rotate-12 rounded-lg bg-sky-300/80 shadow-lg" />
    </div>
  );
}

function GenericReferencePreview({
  metadata,
}: {
  metadata: ChallengeReferenceMetadataValue;
}): React.ReactElement {
  const offset = 12 + (metadata.preview.seed % 12);

  return (
    <div className="absolute inset-x-5 bottom-5 top-14 overflow-hidden rounded-md bg-white/75 p-4 shadow-sm ring-1 ring-black/5 backdrop-blur">
      <div className="flex h-full flex-col justify-between">
        <div>
          <p className="text-xs font-semibold uppercase text-zinc-500">
            {metadata.preview.eyebrow}
          </p>
          <p className="mt-1 text-xl font-semibold text-zinc-950">
            {metadata.preview.title}
          </p>
        </div>
        <div className="flex items-end gap-2">
          <div className="h-12 w-12 rounded-md bg-[var(--reference-accent)]" />
          <div className="h-8 flex-1 rounded-md bg-zinc-950/10" />
          <div className="h-16 w-10 rounded-md bg-zinc-950/15" />
        </div>
      </div>
      <div
        className="absolute h-20 w-20 rounded-full bg-white/70"
        style={{ right: `${offset}px`, top: `${offset + 8}px` }}
      />
    </div>
  );
}
