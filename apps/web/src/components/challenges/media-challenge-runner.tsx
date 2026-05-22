// Client-side prompt run workflow for image and video challenge detail pages.
"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation } from "@tanstack/react-query";
import { CheckCircle2, Loader2, Play, WandSparkles } from "lucide-react";
import { useTranslations } from "next-intl";
import { useMemo, useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";

import { Button, useToast } from "@/components/ui";
import { Link } from "@/i18n/navigation";
import { createPrompteerApiClient, unwrapApiResponse } from "@/lib/api-client";
import type { ChallengeMediaChallenge } from "@/lib/challenge-media";
import { formatMutationError, normalizeError } from "@/lib/errors";
import type { components } from "@prompteer/shared-types";

type ChallengeRunResponse = components["schemas"]["ChallengeRunResponse"];

type MediaChallengeRunnerProps = {
  challenge: ChallengeMediaChallenge;
  kindLabel: string;
  llmEnabled: boolean;
};

type PromptFormValues = {
  prompt: string;
  publishToBoard: boolean;
};

export function MediaChallengeRunner({
  challenge,
  kindLabel,
  llmEnabled,
}: MediaChallengeRunnerProps): React.ReactElement {
  const t = useTranslations("mediaChallenges.runner");
  const { toast } = useToast();
  const promptFormSchema = useMemo(
    () =>
      z.object({
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
  } = useForm<PromptFormValues>({
    defaultValues: {
      prompt: t("defaultPrompt", {
        kind: kindLabel.toLowerCase(),
        title: challenge.title,
      }),
      publishToBoard: true,
    },
    mode: "onChange",
    resolver: zodResolver(promptFormSchema),
  });
  const [error, setError] = useState<string | null>(null);
  const runPromptMutation = useMutation({
    mutationKey: ["challenges", challenge.id, "media-run"],
    mutationFn: runChallengePrompt,
  });
  const promptInput = register("prompt");
  const result = runPromptMutation.data ?? null;
  const isRunning = runPromptMutation.isPending;

  async function runPrompt(values: PromptFormValues): Promise<void> {
    if (!llmEnabled) {
      setError(t("errors.disabled"));
      return;
    }
    setError(null);
    try {
      await runPromptMutation.mutateAsync({
        ...values,
        challengeId: challenge.id,
      });
    } catch (caughtError) {
      const normalizedError = await normalizeError(caughtError);
      if (normalizedError.code === "rate_limited") {
        const message = normalizedError.retryAfterSeconds
          ? t("errors.rateLimitedWithRetry", {
              seconds: normalizedError.retryAfterSeconds,
            })
          : t("errors.rateLimited");
        const formattedMessage = formatMutationError(normalizedError, message);
        setError(formattedMessage);
        toast({
          title: t("errors.rateLimitedTitle"),
          description: formattedMessage,
          variant: "warning",
        });
      } else if (normalizedError.code === "quota_exceeded") {
        const message = formatMutationError(
          normalizedError,
          normalizedError.message || t("errors.quotaExceeded"),
        );
        setError(message);
        toast({
          title: t("errors.quotaExceededTitle"),
          description: message,
          variant: "warning",
        });
      } else if (normalizedError.status === 401) {
        setError(
          formatMutationError(normalizedError, t("errors.unauthorized")),
        );
      } else {
        setError(formatMutationError(normalizedError, t("errors.failed")));
      }
    }
  }

  return (
    <section className="mt-6">
      <form
        aria-busy={isRunning}
        className="rounded-lg border border-zinc-200 bg-white p-6 shadow-sm"
        onSubmit={(event) => void handleSubmit(runPrompt)(event)}
      >
        <div className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_minmax(18rem,0.8fr)]">
          <div>
            <p className="text-sm font-semibold uppercase text-emerald-700">
              {t("eyebrow", { kind: kindLabel })}
            </p>
            <h2 className="mt-2 text-xl font-semibold text-zinc-950">
              {t("title")}
            </h2>
            <p className="mt-2 max-w-2xl text-sm leading-6 text-zinc-600">
              {t("description", { kind: kindLabel.toLowerCase() })}
            </p>

            <label
              className="mt-5 block text-sm font-medium text-zinc-800"
              htmlFor="media-prompt"
            >
              {t("promptLabel")}
            </label>
            <textarea
              className="mt-2 min-h-44 w-full resize-y rounded-md border border-zinc-300 px-3 py-2 text-sm leading-6 text-zinc-950 outline-none transition focus:border-emerald-600 focus:ring-2 focus:ring-emerald-100"
              aria-describedby={
                errors.prompt ? "media-prompt-error" : undefined
              }
              aria-invalid={errors.prompt ? "true" : undefined}
              id="media-prompt"
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
              <p className="mt-2 text-sm text-red-600" id="media-prompt-error">
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
              <p className="mt-3 text-sm text-amber-700">
                {t("disabledNotice")}
              </p>
            ) : null}

            {error ? (
              <p className="mt-4 text-sm text-red-600" role="alert">
                {error}
              </p>
            ) : null}
          </div>

          <div
            aria-live="polite"
            className="min-h-60 rounded-lg border border-zinc-200 bg-zinc-50 p-4"
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
                    {t("tokenCount", {
                      count: totalTokenCount(result.usage),
                    })}
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
                      <span className="font-medium">
                        {t("publishedPrompt")}:
                      </span>{" "}
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
        </div>
      </form>
    </section>
  );
}

async function runChallengePrompt(
  values: PromptFormValues & { challengeId: string },
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

function totalTokenCount(usage: ChallengeRunResponse["usage"]): number {
  if (usage.total_tokens !== undefined) {
    return usage.total_tokens;
  }

  const promptCompletionTokens =
    (usage.prompt_tokens ?? 0) + (usage.completion_tokens ?? 0);
  if (promptCompletionTokens > 0) {
    return promptCompletionTokens;
  }

  const inputOutputTokens =
    (usage.input_tokens ?? 0) + (usage.output_tokens ?? 0);
  if (inputOutputTokens > 0) {
    return inputOutputTokens;
  }

  return Object.values(usage).reduce((sum, value) => sum + value, 0);
}
