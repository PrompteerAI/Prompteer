// Image challenge detail sourced from the API detail endpoint.
import { notFound } from "next/navigation";
import { getTranslations } from "next-intl/server";

import { MediaChallengeDetail } from "@/components/challenges/media-challenge-detail";
import { ApiUnavailable } from "@/components/system/api-unavailable";
import { createPrompteerApiClient, unwrapApiResponse } from "@/lib/api-client";
import { isMediaChallenge, type Challenge } from "@/lib/challenge-media";
import { normalizeError } from "@/lib/errors";

export const dynamic = "force-dynamic";

type Props = {
  params: Promise<{ challengeId: string; locale: string }>;
};

export default async function ImageChallengeDetailPage({
  params,
}: Props): Promise<React.ReactElement> {
  const { challengeId, locale } = await params;
  const t = await getTranslations("mediaChallenges.image");
  const sharedT = await getTranslations("mediaChallenges.shared");
  const challengeTypesT = await getTranslations("challengeTypes");
  const errors = await getTranslations("errors");
  const api = createPrompteerApiClient();
  let challenge: Challenge;
  let features: { llm: boolean };

  try {
    const [challengeResult, featuresResult] = await Promise.all([
      api.GET("/api/v1/challenges/{challenge_id}", {
        params: { path: { challenge_id: challengeId } },
        cache: "no-store",
      }),
      api.GET("/api/v1/config/features", {
        cache: "no-store",
      }),
    ]);
    challenge = unwrapApiResponse(challengeResult) satisfies Challenge;
    features = unwrapApiResponse(featuresResult);
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

  if (!isMediaChallenge(challenge, "img")) {
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
            kindLabel: challengeTypesT("image"),
            levelLabel: sharedT("level"),
            noContent: sharedT("noContent"),
            noReferences: sharedT("noReferences"),
            pathUnavailable: sharedT("pathUnavailable"),
            pathLabel: sharedT("storedPath"),
            previewLabels: {
              generatedLocalImagePreview: sharedT("generatedLocalImagePreview"),
              generatedLocalVideoPreview: sharedT("generatedLocalVideoPreview"),
              imageReference: sharedT("imageReference"),
              launchTeaserSubtitle: sharedT("launchTeaserSubtitle"),
              launchTeaserTitle: sharedT("launchTeaserTitle"),
              productHeroSubtitle: sharedT("productHeroSubtitle"),
              productHeroTitle: sharedT("productHeroTitle"),
              referenceFile: sharedT("referenceFile"),
              videoReference: sharedT("videoReference"),
            },
            referenceLabel: sharedT("reference"),
            referenceUnavailable: sharedT("referenceUnavailable"),
            referencesTitle: sharedT("references"),
            unknownFileType: sharedT("unknownFileType"),
          }}
          kind="img"
          locale={locale}
          llmEnabled={features.llm}
        />
      </div>
    </main>
  );
}
