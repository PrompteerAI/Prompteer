import { ImageIcon, Play, TerminalSquare } from "lucide-react";

import { Link } from "@/i18n/navigation";
import {
  categoryMeta,
  challengeExcerpt,
  challengeReferencePreview,
  levelClass,
  levelLabel,
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
  const meta = categoryMeta[challenge.tag];
  const href = meta.problemRoute(challenge.id);
  const isVideo = challenge.tag === "video";
  const isImage = challenge.tag === "img";
  const referencePreview = challengeReferencePreview(challenge);
  const primaryReference = referencePreview?.primaryReference ?? null;

  if (variant === "media") {
    return (
      <Link className="legacy-category-card" href={href}>
        <div
          className={`legacy-card-media ${isVideo ? "video" : isImage ? "" : "algorithm"}`}
        >
          {primaryReference?.previewUrl && primaryReference.kind === "img" ? (
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
          {primaryReference?.previewUrl && primaryReference.kind === "video" ? (
            <video
              aria-label={`${challenge.title} reference preview`}
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
            {meta.label}
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
              <strong>{referencePreview.countLabel}</strong>
              <span
                style={{
                  display: "block",
                  overflow: "hidden",
                  textOverflow: "ellipsis",
                  whiteSpace: "nowrap",
                }}
              >
                {primaryReference
                  ? `Primary: ${primaryReference.fileType} · ${primaryReference.filePath}`
                  : "No reference file attached"}
              </span>
            </div>
          ) : null}
        </div>
        <div className="legacy-card-body">
          <p className="legacy-pill">Challenge #{challenge.challenge_number}</p>
          <h2>{challenge.title}</h2>
          <p>{challengeExcerpt(challenge)}</p>
          <div className="legacy-card-meta">
            <span className={levelClass(challenge.level)}>
              {levelLabel(challenge.level)}
            </span>
            {iconForTag(challenge.tag)}
          </div>
        </div>
      </Link>
    );
  }

  return (
    <Link className="legacy-challenge-card" href={href}>
      <span className="legacy-pill">
        Challenge #{challenge.challenge_number}
      </span>
      <h2>{challenge.title}</h2>
      <p>{challengeExcerpt(challenge)}</p>
      <div className="legacy-card-meta" style={{ width: "100%" }}>
        <span className={levelClass(challenge.level)}>
          {levelLabel(challenge.level)}
        </span>
        <span className="legacy-pill">{meta.label}</span>
      </div>
    </Link>
  );
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
