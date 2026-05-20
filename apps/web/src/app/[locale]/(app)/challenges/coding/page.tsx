// Coding challenge page for running prompts against seeded problem-solving tasks.
import { getTranslations } from "next-intl/server";

import {
  CodingChallengeRunner,
  type Challenge,
} from "@/components/challenges/coding-challenge-runner";
import { createPrompteerApiClient, unwrapApiResponse } from "@/lib/api-client";

export const dynamic = "force-dynamic";

export default async function CodingChallengesPage(): Promise<React.ReactElement> {
  const t = await getTranslations("coding");
  const api = createPrompteerApiClient();
  const [challengesResult, featuresResult] = await Promise.all([
    api.GET("/api/v1/challenges", {
      params: { query: { tag: "ps" } },
      cache: "no-store",
    }),
    api.GET("/api/v1/config/features", {
      cache: "no-store",
    }),
  ]);
  const challenges = unwrapApiResponse(challengesResult) satisfies Challenge[];
  const features = unwrapApiResponse(featuresResult);

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
