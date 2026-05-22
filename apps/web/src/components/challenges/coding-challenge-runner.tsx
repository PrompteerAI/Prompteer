// Client-side prompt editor and run workflow for coding challenges.
"use client";

// Prompt runner UI for seeded coding challenges and deterministic LLM feedback.
import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation } from "@tanstack/react-query";
import { CheckCircle2, Loader2, Play, WandSparkles } from "lucide-react";
import { useTranslations } from "next-intl";
import { useMemo, useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";

import { Badge, Button, Card, useToast } from "@/components/ui";
import { Link } from "@/i18n/navigation";
import { createPrompteerApiClient, unwrapApiResponse } from "@/lib/api-client";
import { normalizeError } from "@/lib/errors";
import type { components } from "@prompteer/shared-types";

export type Challenge = components["schemas"]["ChallengeRead"];
type ChallengeRunResponse = components["schemas"]["ChallengeRunResponse"];

interface CodingChallengeRunnerProps {
  challenges: Challenge[];
  llmEnabled: boolean;
}

type PromptFormValues = {
  challengeId: string;
  prompt: string;
  publishToBoard: boolean;
};

export function CodingChallengeRunner({
  challenges,
  llmEnabled,
}: CodingChallengeRunnerProps): React.ReactElement {
  const t = useTranslations("coding.runner");
  const { toast } = useToast();
  const promptFormSchema = useMemo(
    () =>
      z.object({
        challengeId: z.string().min(1, t("errors.noChallenge")),
        prompt: z.string().trim().min(10, t("errors.shortPrompt")),
        publishToBoard: z.boolean(),
      }),
    [t],
  );
  const {
    formState: { errors, isValid },
    handleSubmit,
    register,
    setValue,
    watch,
  } = useForm<PromptFormValues>({
    defaultValues: {
      challengeId: challenges[0]?.id ?? "",
      prompt: t("defaultPrompt"),
      publishToBoard: true,
    },
    mode: "onChange",
    resolver: zodResolver(promptFormSchema),
  });
  const [error, setError] = useState<string | null>(null);
  const runPromptMutation = useMutation({
    mutationKey: ["challenges", "run"],
    mutationFn: runChallengePrompt,
  });
  const selectedChallengeId = watch("challengeId");
  const promptInput = register("prompt");
  const result = runPromptMutation.data ?? null;
  const isRunning = runPromptMutation.isPending;

  const selectedChallenge = useMemo(
    () =>
      challenges.find((challenge) => challenge.id === selectedChallengeId) ??
      challenges[0],
    [challenges, selectedChallengeId],
  );

  async function runPrompt(values: PromptFormValues): Promise<void> {
    if (!llmEnabled) {
      setError(t("errors.disabled"));
      return;
    }
    if (!selectedChallenge) {
      setError(t("errors.noChallenge"));
      return;
    }
    setError(null);
    try {
      await runPromptMutation.mutateAsync(values);
    } catch (caughtError) {
      const normalizedError = await normalizeError(caughtError);
      if (normalizedError.code === "rate_limited") {
        const message = normalizedError.retryAfterSeconds
          ? t("errors.rateLimitedWithRetry", {
              seconds: normalizedError.retryAfterSeconds,
            })
          : t("errors.rateLimited");
        setError(message);
        toast({
          title: t("errors.rateLimitedTitle"),
          description: message,
          variant: "warning",
        });
      } else if (normalizedError.code === "quota_exceeded") {
        const message = normalizedError.message || t("errors.quotaExceeded");
        setError(message);
        toast({
          title: t("errors.quotaExceededTitle"),
          description: message,
          variant: "warning",
        });
      } else if (normalizedError.status === 401) {
        setError(t("errors.unauthorized"));
      } else {
        setError(t("errors.failed"));
      }
    }
  }

  if (!selectedChallenge) {
    return (
      <Card className="p-6">
        <h1 className="text-2xl font-semibold text-zinc-950">
          {t("emptyTitle")}
        </h1>
        <p className="mt-3 text-sm leading-6 text-zinc-600">
          {t("emptyDescriptionBefore")} <code>make seed</code>{" "}
          {t("emptyDescriptionAfter")}
        </p>
      </Card>
    );
  }

  return (
    <section className="grid gap-6 lg:grid-cols-[minmax(0,0.9fr)_minmax(0,1.1fr)]">
      <Card className="p-6">
        <div className="flex items-start justify-between gap-4">
          <div>
            <p className="text-sm font-medium uppercase text-emerald-700">
              {t("challengeEyebrow", {
                number: selectedChallenge.challenge_number,
              })}
            </p>
            <h2 className="mt-2 text-2xl font-semibold text-zinc-950">
              {selectedChallenge.title}
            </h2>
          </div>
          <Badge className="capitalize" variant="outline">
            {selectedChallenge.level}
          </Badge>
        </div>

        <label
          className="mt-6 block text-sm font-medium text-zinc-800"
          htmlFor="challenge"
        >
          {t("challengeLabel")}
        </label>
        <select
          className="mt-2 min-h-11 w-full rounded-md border border-zinc-300 bg-white px-3 text-sm text-zinc-950"
          aria-describedby={errors.challengeId ? "challenge-error" : undefined}
          aria-invalid={errors.challengeId ? "true" : undefined}
          id="challenge"
          {...register("challengeId")}
        >
          {challenges.map((challenge) => (
            <option key={challenge.id} value={challenge.id}>
              #{challenge.challenge_number} {challenge.title}
            </option>
          ))}
        </select>
        {errors.challengeId ? (
          <p className="mt-2 text-sm text-red-600" id="challenge-error">
            {errors.challengeId.message}
          </p>
        ) : null}

        <p className="mt-6 text-sm leading-6 text-zinc-600">
          {selectedChallenge.content ?? t("noInstructions")}
        </p>
      </Card>

      <form
        aria-busy={isRunning}
        className="rounded-lg border border-zinc-200 bg-white p-6 shadow-sm"
        onSubmit={(event) => void handleSubmit(runPrompt)(event)}
      >
        <label className="text-sm font-medium text-zinc-800" htmlFor="prompt">
          {t("promptLabel")}
        </label>
        <textarea
          className="mt-2 min-h-44 w-full resize-y rounded-md border border-zinc-300 px-3 py-2 text-sm leading-6 text-zinc-950 outline-none transition focus:border-emerald-600 focus:ring-2 focus:ring-emerald-100"
          aria-describedby={errors.prompt ? "prompt-error" : undefined}
          aria-invalid={errors.prompt ? "true" : undefined}
          id="prompt"
          {...promptInput}
          onInput={(event) => {
            setValue("prompt", event.currentTarget.value, {
              shouldDirty: true,
              shouldTouch: true,
              shouldValidate: true,
            });
          }}
        />
        {errors.prompt ? (
          <p className="mt-2 text-sm text-red-600" id="prompt-error">
            {errors.prompt.message}
          </p>
        ) : null}
        <label className="mt-4 flex items-start gap-3 rounded-md border border-zinc-200 bg-zinc-50 px-3 py-3 text-sm text-zinc-700">
          <input
            className="mt-0.5 h-4 w-4 rounded border-zinc-300 text-emerald-700 focus:ring-emerald-600"
            type="checkbox"
            {...register("publishToBoard")}
          />
          <span>
            <span className="block font-medium text-zinc-900">
              {t("publishLabel")}
            </span>
            <span className="mt-1 block leading-5">
              {t("publishDescription")}
            </span>
          </span>
        </label>
        <Button
          className="mt-4 min-h-11 px-4"
          disabled={!llmEnabled || isRunning || !isValid}
          type="submit"
        >
          {isRunning ? (
            <Loader2 aria-hidden="true" className="h-4 w-4 animate-spin" />
          ) : (
            <Play aria-hidden="true" className="h-4 w-4" />
          )}
          {t("run")}
        </Button>

        {!llmEnabled ? (
          <p className="mt-3 text-sm text-amber-700">{t("disabledNotice")}</p>
        ) : null}

        {error ? (
          <p className="mt-4 text-sm text-red-600" role="alert">
            {error}
          </p>
        ) : null}

        <div
          aria-live="polite"
          className="mt-6 min-h-40 rounded-lg border border-zinc-200 bg-zinc-50 p-4"
        >
          {result ? (
            <>
              <div className="flex items-center justify-between gap-3">
                <div className="flex items-center gap-2 text-sm font-medium text-zinc-900">
                  <WandSparkles
                    aria-hidden="true"
                    className="h-4 w-4 text-emerald-700"
                  />
                  {t("resultTitle")}
                </div>
                <span className="text-xs text-zinc-500">
                  {t("tokenCount", { count: result.usage.total_tokens })}
                </span>
              </div>
              <p className="mt-3 whitespace-pre-wrap break-words text-sm leading-6 text-zinc-700">
                {result.output}
              </p>
              {result.share ? (
                <div className="mt-4 flex flex-wrap items-center gap-3 rounded-md border border-emerald-200 bg-emerald-50 px-3 py-2 text-sm text-emerald-900">
                  <span className="inline-flex items-center gap-2 font-medium">
                    <CheckCircle2 aria-hidden="true" className="h-4 w-4" />
                    {t("published")}
                  </span>
                  <Link
                    className="inline-flex min-h-11 items-center font-medium underline underline-offset-4 hover:text-emerald-700"
                    href="/board"
                  >
                    {t("viewBoard")}
                  </Link>
                  <span className="basis-full text-emerald-950">
                    <span className="font-medium">{t("publishedPrompt")}:</span>{" "}
                    {result.prompt}
                  </span>
                </div>
              ) : (
                <p className="mt-4 text-sm text-zinc-500">
                  {t("notPublished")}
                </p>
              )}
            </>
          ) : (
            <p className="text-sm leading-6 text-zinc-500">
              {t("emptyResult")}
            </p>
          )}
        </div>
      </form>
    </section>
  );
}

async function runChallengePrompt(
  values: PromptFormValues,
): Promise<ChallengeRunResponse> {
  const api = createPrompteerApiClient();
  return unwrapApiResponse(
    await api.POST("/api/v1/challenges/{challenge_id}/run", {
      params: { path: { challenge_id: values.challengeId } },
      body: {
        prompt: values.prompt,
        publish_to_board: values.publishToBoard,
      },
    }),
  );
}
