// Read-only video challenge detail sourced from the API detail endpoint.
import { notFound } from "next/navigation";
import { getTranslations } from "next-intl/server";

import { MediaChallengeDetail } from "@/components/challenges/media-challenge-detail";
import { ApiUnavailable } from "@/components/system/api-unavailable";
import { createPrompteerApiClient, unwrapApiResponse } from "@/lib/api-client";
import { isMediaChallenge, type Challenge } from "@/lib/challenge-media";
import { normalizeError } from "@/lib/errors";

export const dynamic = "force-dynamic";

type Props = {
  params: Promise<{ challengeId: string }>;
};

export default async function VideoChallengeDetailPage({
  params,
}: Props): Promise<React.ReactElement> {
  const { challengeId } = await params;
  const t = await getTranslations("mediaChallenges.video");
  const sharedT = await getTranslations("mediaChallenges.shared");
  const challengeTypesT = await getTranslations("challengeTypes");
  const errors = await getTranslations("errors");
  const api = createPrompteerApiClient();
  let challenge: Challenge;

  try {
    const challengeResult = await api.GET("/api/v1/challenges/{challenge_id}", {
      params: { path: { challenge_id: challengeId } },
      cache: "no-store",
    });
    challenge = unwrapApiResponse(challengeResult) satisfies Challenge;
  } catch (error) {
    const normalizedError = await normalizeError(error);
    if (normalizedError.status === 404) {
      notFound();
    }
    return (
      <main className="min-h-screen bg-zinc-50 px-6 py-8 text-zinc-950">
        <div className="mx-auto max-w-6xl">
          <ApiUnavailable
            actionLabel={errors("reload")}
            description={errors("apiUnavailableDescription")}
            error={normalizedError}
            requestIdLabel={errors("requestId")}
            title={errors("apiUnavailableTitle")}
          />
        </div>
      </main>
    );
  }

  if (!isMediaChallenge(challenge, "video")) {
    notFound();
  }

  return (
    <main className="min-h-screen bg-zinc-50 px-6 py-8 text-zinc-950">
      <div className="mx-auto max-w-6xl">
        <MediaChallengeDetail
          challenge={challenge}
          copy={{
            backLabel: t("backToList"),
            challengeNumberLabel: sharedT("challengeNumber"),
            contentLabel: sharedT("promptBrief"),
            fallbackReferenceName: (number) =>
              sharedT("referenceFallback", { number }),
            fileTypeLabel: sharedT("fileType"),
            kindLabel: challengeTypesT("video"),
            levelLabel: sharedT("level"),
            noContent: sharedT("noContent"),
            noReferences: sharedT("noReferences"),
            pathUnavailable: sharedT("pathUnavailable"),
            pathLabel: sharedT("storedPath"),
            referenceLabel: sharedT("reference"),
            referenceUnavailable: sharedT("referenceUnavailable"),
            referencesTitle: sharedT("references"),
            unknownFileType: sharedT("unknownFileType"),
          }}
          kind="video"
        />
      </div>
    </main>
  );
}
