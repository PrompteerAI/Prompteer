// Legacy-preview landing route modeled after the original frontend.
import { ImageIcon, TerminalSquare, Video } from "lucide-react";
import { getTranslations } from "next-intl/server";

import { ChallengeCard } from "@/components/legacy/challenge-card";
import { Link } from "@/i18n/navigation";
import { type Challenge, readChallenges } from "@/lib/data";

export const dynamic = "force-dynamic";

export default async function HomePage(): Promise<React.ReactElement> {
  const [t, coding, image, video] = await Promise.all([
    getTranslations("legacy.home"),
    readChallenges("ps"),
    readChallenges("img"),
    readChallenges("video"),
  ]);
  const topChallenges: Challenge[] = [
    coding.at(0),
    image.at(0),
    video.at(0),
  ].filter((challenge): challenge is Challenge => challenge !== undefined);

  return (
    <main className="legacy-main">
      <section className="legacy-section-banner">
        <h1>{t("topTitle")}</h1>
        <p>{t("topDescription")}</p>
      </section>
      <section className="legacy-home-grid" aria-label={t("topAriaLabel")}>
        {topChallenges.map((challenge) => (
          <ChallengeCard
            challenge={challenge}
            key={challenge.id}
            variant="media"
          />
        ))}
      </section>

      <section className="legacy-section-banner compact">
        <h1>{t("categoryTitle")}</h1>
      </section>
      <section
        className="legacy-category-grid"
        aria-label={t("categoryAriaLabel")}
      >
        <CategoryTile
          description={t("categories.algorithm.description")}
          href="/category/coding"
          icon={<TerminalSquare aria-hidden="true" size={32} />}
          title={t("categories.algorithm.title")}
        />
        <CategoryTile
          description={t("categories.image.description")}
          href="/category/image"
          icon={<ImageIcon aria-hidden="true" size={32} />}
          title={t("categories.image.title")}
        />
        <CategoryTile
          description={t("categories.video.description")}
          href="/category/video"
          icon={<Video aria-hidden="true" size={32} />}
          title={t("categories.video.title")}
        />
        <CategoryTile
          description={t("categories.preparing.description")}
          href="/category/preparing"
          title={t("categories.preparing.title")}
        />
      </section>
    </main>
  );
}

function CategoryTile({
  description,
  href,
  icon,
  title,
}: {
  description: string;
  href: string;
  icon?: React.ReactNode;
  title: string;
}): React.ReactElement {
  return (
    <Link className="legacy-category-card" href={href}>
      <div className="legacy-card-body">
        <div className="legacy-card-meta">
          <h2>{title}</h2>
          {icon}
        </div>
        <p>{description}</p>
      </div>
    </Link>
  );
}
