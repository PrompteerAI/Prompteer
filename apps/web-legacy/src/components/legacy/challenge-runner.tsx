"use client";

import { CheckCircle2, Loader2, Play, WandSparkles } from "lucide-react";
import { useMemo, useState } from "react";

import { createPrompteerApiClient, unwrapApiResponse } from "@/lib/api-client";
import { normalizeError } from "@/lib/errors";
import {
  categoryMeta,
  challengeExcerpt,
  levelClass,
  levelLabel,
  type Challenge,
} from "@/lib/legacy";
import type { components } from "@prompteer/shared-types";

type ChallengeRunResponse = components["schemas"]["ChallengeRunResponse"];

interface LegacyChallengeRunnerProps {
  challenge: Challenge;
  llmEnabled: boolean;
}

export function LegacyChallengeRunner({
  challenge,
  llmEnabled,
}: LegacyChallengeRunnerProps): React.ReactElement {
  const [prompt, setPrompt] = useState(defaultPrompt(challenge.tag));
  const [publishToBoard, setPublishToBoard] = useState(true);
  const [result, setResult] = useState<ChallengeRunResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isRunning, setIsRunning] = useState(false);
  const meta = categoryMeta[challenge.tag];
  const mediaMode = challenge.tag === "img" || challenge.tag === "video";
  const canRun = llmEnabled && prompt.trim().length >= 10 && !isRunning;
  const helper = useMemo(() => helperText(challenge.tag), [challenge.tag]);

  async function runPrompt(): Promise<void> {
    if (!canRun) {
      return;
    }
    setError(null);
    setIsRunning(true);
    try {
      const api = createPrompteerApiClient();
      const response = unwrapApiResponse(
        await api.POST("/api/v1/challenges/{challenge_id}/run", {
          params: { path: { challenge_id: challenge.id } },
          body: {
            prompt,
            publish_to_board: publishToBoard,
          },
        }),
      );
      setResult(response);
    } catch (caughtError) {
      const normalized = await normalizeError(caughtError);
      if (normalized.status === 401) {
        setError(
          "Sign in through the primary Prompteer login, then try again.",
        );
      } else {
        setError(normalized.message);
      }
    } finally {
      setIsRunning(false);
    }
  }

  return (
    <main className="legacy-problem-shell">
      <div className="legacy-workspace">
        <aside className="legacy-problem-sidebar">
          <span className="legacy-pill">{meta.eyebrow}</span>
          <h1>
            Challenge #{challenge.challenge_number}
            <br />
            {challenge.title}
          </h1>
          <div className="legacy-card-meta">
            <span className={levelClass(challenge.level)}>
              {levelLabel(challenge.level)}
            </span>
            <span className="legacy-pill">{meta.label}</span>
          </div>
          <section className="legacy-problem-section">
            <h2>Instructions</h2>
            <p>{challengeExcerpt(challenge)}</p>
          </section>
          <section className="legacy-problem-section">
            <h2>Current backend behavior</h2>
            <p>{helper}</p>
          </section>
        </aside>

        <section className="legacy-editor-panel">
          <div className="legacy-card-meta">
            <h2>{mediaMode ? "Prompt" : "Prompt editor"}</h2>
            <span className="legacy-pill">LLM feedback</span>
          </div>
          <textarea
            className="legacy-prompt-area"
            aria-label="Prompt"
            onChange={(event) => setPrompt(event.target.value)}
            value={prompt}
          />
          <label
            style={{
              alignItems: "center",
              display: "flex",
              gap: 10,
              marginTop: 16,
            }}
          >
            <input
              checked={publishToBoard}
              onChange={(event) => setPublishToBoard(event.target.checked)}
              type="checkbox"
            />
            <span>Publish this run to the board</span>
          </label>
          <button
            className="legacy-primary-button"
            disabled={!canRun}
            onClick={() => void runPrompt()}
            style={{ marginTop: 16 }}
            type="button"
          >
            {isRunning ? (
              <Loader2 aria-hidden="true" size={18} />
            ) : (
              <Play aria-hidden="true" size={18} />
            )}
            Run prompt
          </button>
          {!llmEnabled ? (
            <p style={{ color: "#c92a2a" }}>
              Prompt runs are disabled by feature flag.
            </p>
          ) : null}
          {error ? (
            <p role="alert" style={{ color: "#c92a2a" }}>
              {error}
            </p>
          ) : null}
        </section>

        <section className="legacy-result-panel">
          <div className="legacy-card-meta">
            <h2>{mediaMode ? "Preview" : "Result console"}</h2>
            <WandSparkles aria-hidden="true" color="#1971c2" size={20} />
          </div>
          {mediaMode ? (
            <div
              className={`legacy-card-media ${challenge.tag === "video" ? "video" : ""}`}
              style={{ borderRadius: 12, margin: "16px 0", minHeight: 220 }}
            >
              {challenge.tag === "video" ? (
                <span aria-hidden="true" className="legacy-play-symbol" />
              ) : null}
            </div>
          ) : null}
          <div className="legacy-output-area" aria-live="polite">
            {result?.output ??
              "Run a prompt to receive deterministic feedback from the rebuilt backend."}
          </div>
          {result ? (
            <div className="legacy-panel" style={{ marginTop: 16 }}>
              <div className="legacy-card-meta">
                <span>
                  {result.share ? (
                    <CheckCircle2
                      aria-hidden="true"
                      color="#2f9e44"
                      size={18}
                    />
                  ) : null}
                  {result.share ? " Published to board" : " Private run"}
                </span>
                <span className="legacy-pill">
                  {result.usage.total_tokens ?? 0} tokens
                </span>
              </div>
              <p>{result.prompt}</p>
            </div>
          ) : null}
        </section>
      </div>
    </main>
  );
}

function defaultPrompt(tag: Challenge["tag"]): string {
  if (tag === "img") {
    return "Describe the visual goal, composition, key objects, lighting, style, and constraints.";
  }
  if (tag === "video") {
    return "Describe the scene, camera movement, timing, subject action, and visual consistency rules.";
  }
  return "Explain the problem constraints first, then produce a concise solution plan and implementation.";
}

function helperText(tag: Challenge["tag"]): string {
  if (tag === "img") {
    return "Image challenges currently use the shared LLM feedback endpoint; media generation is intentionally not promised by this preview.";
  }
  if (tag === "video") {
    return "Video challenges currently use prompt feedback with video-specific framing, not generated video output.";
  }
  return "Coding challenges run through the LLM mock or configured provider and can publish prompt shares.";
}
