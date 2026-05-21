// Read-only metadata cards for media challenge references. Stored file paths
// are not browser URLs yet, so this component intentionally does not preview
// images or video.
import { FileImage, FileVideo } from "lucide-react";

import {
  referenceMetadata,
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
    <article className="rounded-lg border border-zinc-200 bg-white p-4 shadow-sm">
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
          <p className="mt-2 text-sm text-zinc-600">{unavailableLabel}</p>
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
          <dt className="font-medium text-zinc-500">{pathLabel}</dt>
          <dd className="mt-1 break-words font-mono text-xs text-zinc-900">
            {metadata.filePath}
          </dd>
        </div>
      </dl>
    </article>
  );
}
