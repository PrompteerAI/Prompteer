// Client-side legacy-preview prompt runner shared by coding and media routes.
"use client";

import { CheckCircle2, Loader2, LogIn, Play, WandSparkles } from "lucide-react";
import { useTranslations } from "next-intl";
import { useState } from "react";

import { createPrompteerApiClient, unwrapApiResponse } from "@/lib/api-client";
import { formatMutationError, normalizeError } from "@/lib/errors";
import {
  challengeReferencePreview,
  levelClass,
  normalizeGeneratedRunText,
  type Challenge,
  type ChallengeTag,
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
  const t = useTranslations("legacy.runner");
  const commonT = useTranslations("legacy.common");
  const tagKey = challengeTagKey(challenge.tag);
  const [prompt, setPrompt] = useState(t(`defaultPrompts.${tagKey}`));
  const [publishToBoard, setPublishToBoard] = useState(true);
  const [result, setResult] = useState<ChallengeRunResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isRunning, setIsRunning] = useState(false);
  const mediaMode = challenge.tag === "img" || challenge.tag === "video";
  const referencePreview = challengeReferencePreview(challenge);
  const canRun =
    isAuthenticated && llmEnabled && prompt.trim().length >= 10 && !isRunning;
  const helper = t(`helpers.${tagKey}`);
  const excerpt =
    challenge.content?.replace(/\s+/g, " ").trim() || t("excerptFallback");
  const primaryReference = referencePreview?.primaryReference ?? null;
  const outputText = result?.output
    ? normalizeGeneratedRunText(result.output)
    : t("emptyOutput");

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
        setError(formatMutationError(normalized, t("errors.unauthorized")));
      } else {
        setError(formatMutationError(normalized, normalized.message));
      }
    } finally {
      setIsRunning(false);
    }
  }

  return (
    <main className="legacy-problem-shell">
      <div className="legacy-workspace">
        <aside className="legacy-problem-sidebar">
          <span className="legacy-pill">{t(`eyebrows.${tagKey}`)}</span>
          <h1>
            {t("challengeNumber", { number: challenge.challenge_number })}
            <br />
            {challenge.title}
          </h1>
          <div className="legacy-card-meta">
            <span className={levelClass(challenge.level)}>
              {t(`levels.${challenge.level}`)}
            </span>
            <span className="legacy-pill">{t(`categories.${tagKey}`)}</span>
          </div>
          <section className="legacy-problem-section">
            <h2>{t("instructions")}</h2>
            <p>{excerpt}</p>
          </section>
          <section className="legacy-problem-section">
            <h2>{t("currentBehavior")}</h2>
            <p>{helper}</p>
          </section>
        </aside>

        <section className="legacy-editor-panel">
          <div className="legacy-card-meta">
            <h2>{mediaMode ? t("mediaPromptTitle") : t("editorTitle")}</h2>
            <span className="legacy-pill">{t("feedbackPill")}</span>
          </div>
          <textarea
            className="legacy-prompt-area"
            aria-label={t("promptAriaLabel")}
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
            <span>{t("publishToBoard")}</span>
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
              {t("runPrompt")}
            </button>
          ) : (
            <div className="legacy-login-callout" role="note">
              <p>{t("loginCallout")}</p>
              <div className="legacy-auth-inline-actions">
                <a className="legacy-primary-button" href={demoLoginHref}>
                  <LogIn aria-hidden="true" size={18} />
                  {commonT("demoLogin")}
                </a>
                <a className="legacy-secondary-button" href={loginHref}>
                  {commonT("primaryLogin")}
                </a>
              </div>
            </div>
          )}
          {!llmEnabled ? (
            <p style={{ color: "#c92a2a" }}>{t("featureDisabled")}</p>
          ) : null}
          {error ? (
            <p role="alert" style={{ color: "#c92a2a" }}>
              {error}
            </p>
          ) : null}
        </section>

        <section className="legacy-result-panel">
          <div className="legacy-card-meta">
            <h2>{mediaMode ? t("previewTitle") : t("resultTitle")}</h2>
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
                // eslint-disable-next-line @next/next/no-img-element -- Mock media can be data URLs, so Next image optimization is not useful here.
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
                  aria-label={t("referencePreviewLabel", {
                    title: challenge.title,
                  })}
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
              aria-label={t("referenceMetadataLabel")}
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
              <strong>
                {t("referenceCount", {
                  count: referencePreview.references.length,
                })}
              </strong>
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
                        {t("referenceItem", { number: index + 1 })}
                      </span>{" "}
                      <span style={{ overflowWrap: "anywhere" }}>
                        {t("referenceFile", {
                          filePath: reference.filePath,
                          fileType: reference.fileType,
                        })}
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
                  {t("noReferenceFile")}
                </span>
              )}
            </div>
          ) : null}
          <div className="legacy-output-area" aria-live="polite">
            {outputText}
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
                  {result.share ? t("published") : t("privateRun")}
                </span>
                <span className="legacy-pill">
                  {t("tokenCount", {
                    count: result.usage.total_tokens ?? 0,
                  })}
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

function challengeTagKey(tag: ChallengeTag): "coding" | "image" | "video" {
  if (tag === "img") {
    return "image";
  }
  if (tag === "video") {
    return "video";
  }
  return "coding";
}
