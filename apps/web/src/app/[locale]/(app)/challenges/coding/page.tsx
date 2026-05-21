// Coding challenge page for running prompts against seeded problem-solving tasks.
import { getTranslations } from "next-intl/server";

import {
  CodingChallengeRunner,
  type Challenge,
} from "@/components/challenges/coding-challenge-runner";
import { ApiUnavailable } from "@/components/system/api-unavailable";
import { createPrompteerApiClient, unwrapApiResponse } from "@/lib/api-client";
import { normalizeError } from "@/lib/errors";

export const dynamic = "force-dynamic";

export default async function CodingChallengesPage(): Promise<React.ReactElement> {
  const t = await getTranslations("coding");
  const errors = await getTranslations("errors");
  const api = createPrompteerApiClient();
  let challenges: Challenge[];
  let features: { llm: boolean };

  try {
    const [challengesResult, featuresResult] = await Promise.all([
      api.GET("/api/v1/challenges", {
        params: { query: { tag: "ps" } },
        cache: "no-store",
      }),
      api.GET("/api/v1/config/features", {
        cache: "no-store",
      }),
    ]);
    challenges = unwrapApiResponse(challengesResult) satisfies Challenge[];
    features = unwrapApiResponse(featuresResult);
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
        <CodingChallengeRunner
          challenges={challenges}
          llmEnabled={features.llm}
        />
      </div>
    </main>
  );
}
