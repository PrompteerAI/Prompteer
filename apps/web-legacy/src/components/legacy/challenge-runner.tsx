"use client";

import { CheckCircle2, Loader2, LogIn, Play, WandSparkles } from "lucide-react";
import { useMemo, useState } from "react";

import { createPrompteerApiClient, unwrapApiResponse } from "@/lib/api-client";
import { normalizeError } from "@/lib/errors";
import {
  categoryMeta,
  challengeExcerpt,
  challengeReferencePreview,
  levelClass,
  levelLabel,
  type Challenge,
} from "@/lib/legacy";
import type { components } from "@prompteer/shared-types";

type ChallengeRunResponse = components["schemas"]["ChallengeRunResponse"];

interface LegacyChallengeRunnerProps {
  challenge: Challenge;
  demoLoginHref: string;
  isAuthenticated: boolean;
  llmEnabled: boolean;
  loginHref: string;
}

export function LegacyChallengeRunner({
  challenge,
  demoLoginHref,
  isAuthenticated,
  llmEnabled,
  loginHref,
}: LegacyChallengeRunnerProps): React.ReactElement {
  const [prompt, setPrompt] = useState(defaultPrompt(challenge.tag));
  const [publishToBoard, setPublishToBoard] = useState(true);
  const [result, setResult] = useState<ChallengeRunResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isRunning, setIsRunning] = useState(false);
  const meta = categoryMeta[challenge.tag];
  const mediaMode = challenge.tag === "img" || challenge.tag === "video";
  const referencePreview = challengeReferencePreview(challenge);
  const canRun =
    isAuthenticated && llmEnabled && prompt.trim().length >= 10 && !isRunning;
  const helper = useMemo(() => helperText(challenge.tag), [challenge.tag]);
  const primaryReference = referencePreview?.primaryReference ?? null;

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
          {isAuthenticated ? (
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
          ) : (
            <div className="legacy-login-callout" role="note">
              <p>
                Sign in before running prompts. The legacy preview will reuse
                the primary Prompteer Auth.js session through the gateway.
              </p>
              <div className="legacy-auth-inline-actions">
                <a className="legacy-primary-button" href={demoLoginHref}>
                  <LogIn aria-hidden="true" size={18} />
                  Demo login
                </a>
                <a className="legacy-secondary-button" href={loginHref}>
                  Primary login
                </a>
              </div>
            </div>
          )}
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
              style={{
                borderRadius: 12,
                margin: "16px 0",
                minHeight: 220,
                overflow: "hidden",
              }}
            >
              {primaryReference?.previewUrl &&
              primaryReference.kind === "img" ? (
                // eslint-disable-next-line @next/next/no-img-element
                <img
                  alt=""
                  src={primaryReference.previewUrl}
                  style={{
                    height: "100%",
                    inset: 0,
                    objectFit: "cover",
                    position: "absolute",
                    width: "100%",
                    zIndex: 1,
                  }}
                />
              ) : null}
              {primaryReference?.previewUrl &&
              primaryReference.kind === "video" ? (
                <video
                  aria-label={`${challenge.title} reference preview`}
                  controls
                  muted
                  playsInline
                  preload="metadata"
                  src={primaryReference.previewUrl}
                  style={{
                    height: "100%",
                    inset: 0,
                    objectFit: "cover",
                    position: "absolute",
                    width: "100%",
                    zIndex: 1,
                  }}
                />
              ) : null}
              {challenge.tag === "video" && !primaryReference?.previewUrl ? (
                <span aria-hidden="true" className="legacy-play-symbol" />
              ) : null}
            </div>
          ) : null}
          {referencePreview ? (
            <div
              aria-label="Reference metadata"
              style={{
                background: "#ffffff",
                border: "1px solid var(--legacy-border)",
                borderRadius: 12,
                color: "#1f2937",
                fontSize: 13,
                lineHeight: 1.45,
                margin: "0 0 16px",
                padding: "12px 14px",
              }}
            >
              <strong>{referencePreview.countLabel}</strong>
              {referencePreview.references.length > 0 ? (
                <ul
                  style={{
                    display: "grid",
                    gap: 6,
                    listStyle: "none",
                    margin: "8px 0 0",
                    padding: 0,
                  }}
                >
                  {referencePreview.references.map((reference, index) => (
                    <li key={`${reference.filePath}-${index}`}>
                      <span style={{ fontWeight: 700 }}>
                        Reference {index + 1}:
                      </span>{" "}
                      <span style={{ overflowWrap: "anywhere" }}>
                        {reference.fileType} · {reference.filePath}
                      </span>
                    </li>
                  ))}
                </ul>
              ) : (
                <span
                  style={{
                    display: "block",
                    marginTop: 8,
                  }}
                >
                  No reference file attached
                </span>
              )}
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
