// Legacy-preview image challenge category route.
import { getTranslations } from "next-intl/server";

import { ChallengeCard } from "@/components/legacy/challenge-card";
import { Link } from "@/i18n/navigation";
import { readChallenges } from "@/lib/data";

export const dynamic = "force-dynamic";

export default async function ImageCategoryPage(): Promise<React.ReactElement> {
  const [t, commonT, challenges] = await Promise.all([
    getTranslations("legacy.categories.image"),
    getTranslations("legacy.common"),
    readChallenges("img"),
  ]);
  const featured = challenges[0];

  return (
    <main className="legacy-page">
      <section className="legacy-featured-banner">
        <span className="legacy-pill">{commonT("featured")}</span>
        <h1>{t("title")}</h1>
        <p>{t("description")}</p>
        {featured ? (
          <Link
            className="legacy-primary-button"
            href={`/image/challenge/${featured.id}`}
            style={{ marginTop: 24 }}
          >
            {commonT("challengeNow")}
          </Link>
        ) : null}
      </section>
      <div className="legacy-toolbar">
        <input
          className="legacy-search"
          placeholder={t("searchPlaceholder")}
          readOnly
        />
        <div className="legacy-filter-group">
          <button className="legacy-filter-button active" type="button">
            {t("imageFilter")}
          </button>
          <Link className="legacy-filter-button" href="/category/video">
            {t("videoFilter")}
          </Link>
        </div>
      </div>
      <section className="legacy-home-grid">
        {challenges.map((challenge) => (
          <ChallengeCard
            challenge={challenge}
            key={challenge.id}
            variant="media"
          />
        ))}
      </section>
    </main>
  );
}
