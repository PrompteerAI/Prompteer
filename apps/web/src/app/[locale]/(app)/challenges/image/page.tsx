// Read-only image challenge list sourced from the API challenge tag filter.
import { getTranslations } from "next-intl/server";

import { ChallengeTypeNav } from "@/components/challenges/challenge-type-nav";
import { MediaChallengeList } from "@/components/challenges/media-challenge-list";
import { ApiUnavailable } from "@/components/system/api-unavailable";
import { createPrompteerApiClient, unwrapApiResponse } from "@/lib/api-client";
import { isMediaChallenge, type Challenge } from "@/lib/challenge-media";
import { normalizeError } from "@/lib/errors";

export const dynamic = "force-dynamic";

export default async function ImageChallengesPage(): Promise<React.ReactElement> {
  const t = await getTranslations("mediaChallenges.image");
  const sharedT = await getTranslations("mediaChallenges.shared");
  const challengeTypesT = await getTranslations("challengeTypes");
  const errors = await getTranslations("errors");
  const api = createPrompteerApiClient();
  let challenges: Challenge[];

  try {
    const challengesResult = await api.GET("/api/v1/challenges", {
      params: { query: { tag: "img" } },
      cache: "no-store",
    });
    challenges = unwrapApiResponse(challengesResult) satisfies Challenge[];
  } catch (error) {
    const normalizedError = await normalizeError(error);
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

  return (
    <main className="min-h-screen bg-zinc-50 px-6 py-8 text-zinc-950">
      <div className="mx-auto max-w-6xl">
        <div className="mb-6">
          <p className="text-sm font-semibold uppercase text-emerald-700">
            {t("eyebrow")}
          </p>
          <h1 className="mt-2 text-3xl font-semibold">{t("title")}</h1>
          <p className="mt-3 max-w-2xl text-sm leading-6 text-zinc-600">
            {t("description")}
          </p>
        </div>
        <ChallengeTypeNav
          active="image"
          labels={{
            coding: challengeTypesT("coding"),
            image: challengeTypesT("image"),
            video: challengeTypesT("video"),
          }}
          navLabel={challengeTypesT("navLabel")}
        />
        <MediaChallengeList
          challenges={challenges.filter((challenge) =>
            isMediaChallenge(challenge, "img"),
          )}
          copy={{
            emptyTitle: t("emptyTitle"),
            emptyDescription: t("emptyDescription"),
            fallbackReferenceName: (number) =>
              sharedT("referenceFallback", { number }),
            levelLabel: sharedT("level"),
            kindLabel: challengeTypesT("image"),
            noContent: sharedT("noContent"),
            noReferences: sharedT("noReferences"),
            openLabel: t("openDetail"),
            pathUnavailable: sharedT("pathUnavailable"),
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
            referencesLabel: sharedT("references"),
            fileTypeLabel: sharedT("fileType"),
            pathLabel: sharedT("storedPath"),
            unknownFileType: sharedT("unknownFileType"),
          }}
          kind="img"
        />
      </div>
    </main>
  );
}
