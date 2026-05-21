// Legacy-preview challenge card used by category and media listing routes.
import { ImageIcon, Play, TerminalSquare } from "lucide-react";
import { useTranslations } from "next-intl";

import { Link } from "@/i18n/navigation";
import {
  categoryMeta,
  challengeReferencePreview,
  levelClass,
  type Challenge,
  type ChallengeTag,
} from "@/lib/legacy";

interface ChallengeCardProps {
  challenge: Challenge;
  variant?: "compact" | "media";
}

export function ChallengeCard({
  challenge,
  variant = "compact",
}: ChallengeCardProps): React.ReactElement {
  const t = useTranslations("legacy.challenge");
  const meta = categoryMeta[challenge.tag];
  const href = meta.problemRoute(challenge.id);
  const isVideo = challenge.tag === "video";
  const isImage = challenge.tag === "img";
  const referencePreview = challengeReferencePreview(challenge);
  const primaryReference = referencePreview?.primaryReference ?? null;
  const excerpt =
    challenge.content?.replace(/\s+/g, " ").trim() || t("excerptFallback");
  const categoryLabel = t(`categories.${categoryKey(challenge.tag)}`);
  const difficultyLabel = t(`levels.${challenge.level}`);
  const challengeNumber = t("number", {
    number: challenge.challenge_number,
  });

  if (variant === "media") {
    return (
      <Link className="legacy-category-card" href={href}>
        <div
          className={`legacy-card-media ${isVideo ? "video" : isImage ? "" : "algorithm"}`}
        >
          {primaryReference?.previewUrl && primaryReference.kind === "img" ? (
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
          {primaryReference?.previewUrl && primaryReference.kind === "video" ? (
            <video
              aria-label={t("referencePreviewLabel", {
                title: challenge.title,
              })}
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
          {isVideo ? (
            <span aria-hidden="true" className="legacy-play-symbol" />
          ) : null}
          <span
            className="legacy-pill"
            style={{ position: "absolute", right: 18, top: 18, zIndex: 2 }}
          >
            {categoryLabel}
          </span>
          {referencePreview ? (
            <div
              style={{
                background: "rgb(255 255 255 / 0.88)",
                borderRadius: 8,
                bottom: 16,
                color: "#1f2937",
                fontSize: 12,
                left: 16,
                lineHeight: 1.35,
                maxWidth: "calc(100% - 32px)",
                padding: "8px 10px",
                position: "absolute",
                right: 16,
                zIndex: 2,
              }}
            >
              <strong>
                {t("referenceCount", {
                  count: referencePreview.references.length,
                })}
              </strong>
              <span
                style={{
                  display: "block",
                  overflow: "hidden",
                  textOverflow: "ellipsis",
                  whiteSpace: "nowrap",
                }}
              >
                {primaryReference
                  ? t("primaryReference", {
                      filePath: primaryReference.filePath,
                      fileType: primaryReference.fileType,
                    })
                  : t("noReferenceFile")}
              </span>
            </div>
          ) : null}
        </div>
        <div className="legacy-card-body">
          <p className="legacy-pill">{challengeNumber}</p>
          <h2>{challenge.title}</h2>
          <p>{excerpt}</p>
          <div className="legacy-card-meta">
            <span className={levelClass(challenge.level)}>
              {difficultyLabel}
            </span>
            {iconForTag(challenge.tag)}
          </div>
        </div>
      </Link>
    );
  }

  return (
    <Link className="legacy-challenge-card" href={href}>
      <span className="legacy-pill">{challengeNumber}</span>
      <h2>{challenge.title}</h2>
      <p>{excerpt}</p>
      <div className="legacy-card-meta" style={{ width: "100%" }}>
        <span className={levelClass(challenge.level)}>{difficultyLabel}</span>
        <span className="legacy-pill">{categoryLabel}</span>
      </div>
    </Link>
  );
}

function categoryKey(tag: ChallengeTag): "algorithm" | "image" | "video" {
  if (tag === "img") {
    return "image";
  }
  if (tag === "video") {
    return "video";
  }
  return "algorithm";
}

function iconForTag(tag: ChallengeTag): React.ReactElement {
  if (tag === "video") {
    return <Play aria-hidden="true" size={20} />;
  }
  if (tag === "img") {
    return <ImageIcon aria-hidden="true" size={20} />;
  }
  return <TerminalSquare aria-hidden="true" size={20} />;
}
