import { ImageIcon, Play, TerminalSquare } from "lucide-react";

import { Link } from "@/i18n/navigation";
import {
  categoryMeta,
  challengeExcerpt,
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

  if (variant === "media") {
    return (
      <Link className="legacy-category-card" href={href}>
        <div
          className={`legacy-card-media ${isVideo ? "video" : isImage ? "" : "algorithm"}`}
        >
          {isVideo ? (
            <span aria-hidden="true" className="legacy-play-symbol" />
          ) : null}
          <span
            className="legacy-pill"
            style={{ position: "absolute", right: 18, top: 18, zIndex: 2 }}
          >
            {meta.label}
          </span>
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
