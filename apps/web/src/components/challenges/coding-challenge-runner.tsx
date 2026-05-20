"use client";

import { Loader2, Play, WandSparkles } from "lucide-react";
import { useMemo, useState } from "react";

import { apiPost } from "@/lib/api-client";
import { normalizeError } from "@/lib/errors";

export interface Challenge {
  id: string;
  challenge_number: number;
  tag: "ps" | "img" | "video";
  level: "easy" | "medium" | "hard";
  title: string;
  content: string | null;
}

interface ChallengeRunResponse {
  challenge: Challenge;
  prompt: string;
  provider: string;
  output: string;
  usage: {
    prompt_tokens: number;
    completion_tokens: number;
    total_tokens: number;
  };
}

interface CodingChallengeRunnerProps {
  challenges: Challenge[];
  llmEnabled: boolean;
}

export function CodingChallengeRunner({
  challenges,
  llmEnabled,
}: CodingChallengeRunnerProps): React.ReactElement {
  const [selectedChallengeId, setSelectedChallengeId] = useState(
    challenges[0]?.id ?? "",
  );
  const [prompt, setPrompt] = useState(
    "Explain the FizzBuzz rules first, then produce concise Python with clear edge cases.",
  );
  const [result, setResult] = useState<ChallengeRunResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isRunning, setIsRunning] = useState(false);

  const selectedChallenge = useMemo(
    () =>
      challenges.find((challenge) => challenge.id === selectedChallengeId) ??
      challenges[0],
    [challenges, selectedChallengeId],
  );

  async function runPrompt(
    event: React.FormEvent<HTMLFormElement>,
  ): Promise<void> {
    event.preventDefault();
    if (!llmEnabled) {
      setError("Prompt runs are disabled for this environment.");
      return;
    }
    if (!selectedChallenge || prompt.trim().length < 10) {
      setError("Write a prompt with at least 10 characters.");
      return;
    }
    setIsRunning(true);
    setError(null);
    try {
      const response = await apiPost<ChallengeRunResponse>(
        `/challenges/${selectedChallenge.id}/run`,
        { prompt },
      );
      setResult(response);
    } catch (caughtError) {
      const normalizedError = await normalizeError(caughtError);
      if (normalizedError.code === "rate_limited") {
        setError(
          "Prompt runs are temporarily rate limited. Wait a moment, then try again.",
        );
      } else if (normalizedError.code === "quota_exceeded") {
        setError(normalizedError.message);
      } else if (normalizedError.status === 401) {
        setError("Sign in before running a prompt.");
      } else {
        setError(
          "The prompt run failed. Check that the API server and seed data are running.",
        );
      }
    } finally {
      setIsRunning(false);
    }
  }

  if (!selectedChallenge) {
    return (
      <section className="rounded-lg border border-zinc-200 bg-white p-6 shadow-sm">
        <h1 className="text-2xl font-semibold text-zinc-950">
          Coding challenges
        </h1>
        <p className="mt-3 text-sm leading-6 text-zinc-600">
          No coding challenges are available yet. Run <code>make seed</code> to
          create demo data.
        </p>
      </section>
    );
  }

  return (
    <section className="grid gap-6 lg:grid-cols-[minmax(0,0.9fr)_minmax(0,1.1fr)]">
      <div className="rounded-lg border border-zinc-200 bg-white p-6 shadow-sm">
        <div className="flex items-start justify-between gap-4">
          <div>
            <p className="text-sm font-medium uppercase text-emerald-700">
              Challenge #{selectedChallenge.challenge_number}
            </p>
            <h1 className="mt-2 text-2xl font-semibold text-zinc-950">
              {selectedChallenge.title}
            </h1>
          </div>
          <span className="rounded-md border border-zinc-200 px-2.5 py-1 text-xs font-medium capitalize text-zinc-700">
            {selectedChallenge.level}
          </span>
        </div>

        <label
          className="mt-6 block text-sm font-medium text-zinc-800"
          htmlFor="challenge"
        >
          Challenge
        </label>
        <select
          className="mt-2 h-10 w-full rounded-md border border-zinc-300 bg-white px-3 text-sm text-zinc-950"
          id="challenge"
          onChange={(event) => setSelectedChallengeId(event.target.value)}
          value={selectedChallenge.id}
        >
          {challenges.map((challenge) => (
            <option key={challenge.id} value={challenge.id}>
              #{challenge.challenge_number} {challenge.title}
            </option>
          ))}
        </select>

        <p className="mt-6 text-sm leading-6 text-zinc-600">
          {selectedChallenge.content ?? "No additional instructions."}
        </p>
      </div>

      <form
        className="rounded-lg border border-zinc-200 bg-white p-6 shadow-sm"
        onSubmit={(event) => {
          void runPrompt(event);
        }}
      >
        <label className="text-sm font-medium text-zinc-800" htmlFor="prompt">
          Prompt
        </label>
        <textarea
          className="mt-2 min-h-44 w-full resize-y rounded-md border border-zinc-300 px-3 py-2 text-sm leading-6 text-zinc-950 outline-none transition focus:border-emerald-600 focus:ring-2 focus:ring-emerald-100"
          id="prompt"
          onChange={(event) => setPrompt(event.target.value)}
          value={prompt}
        />
        <button
          className="mt-4 inline-flex h-10 items-center gap-2 rounded-md bg-zinc-950 px-4 text-sm font-medium text-white transition hover:bg-zinc-800 disabled:cursor-not-allowed disabled:bg-zinc-400"
          disabled={!llmEnabled || isRunning || prompt.trim().length < 10}
          type="submit"
        >
          {isRunning ? (
            <Loader2 aria-hidden="true" className="h-4 w-4 animate-spin" />
          ) : (
            <Play aria-hidden="true" className="h-4 w-4" />
          )}
          Run prompt
        </button>

        {!llmEnabled ? (
          <p className="mt-3 text-sm text-amber-700">
            Prompt runs are disabled by the environment feature flags.
          </p>
        ) : null}

        {error ? <p className="mt-4 text-sm text-red-600">{error}</p> : null}

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
                  Mock run result
                </div>
                <span className="text-xs text-zinc-500">
                  {result.usage.total_tokens} tokens
                </span>
              </div>
              <p className="mt-3 whitespace-pre-wrap break-words text-sm leading-6 text-zinc-700">
                {result.output}
              </p>
            </>
          ) : (
            <p className="text-sm leading-6 text-zinc-500">
              Run a prompt to see deterministic feedback from the local LLM
              mock.
            </p>
          )}
        </div>
      </form>
    </section>
  );
}
