// Legacy-preview coding challenge category route.
import { getTranslations } from "next-intl/server";

import { ChallengeCard } from "@/components/legacy/challenge-card";
import { Link } from "@/i18n/navigation";
import { readChallenges } from "@/lib/data";

export const dynamic = "force-dynamic";

export default async function CodingCategoryPage(): Promise<React.ReactElement> {
  const [t, commonT, challenges] = await Promise.all([
    getTranslations("legacy.categories.coding"),
    getTranslations("legacy.common"),
    readChallenges("ps"),
  ]);
  const featured = challenges[0];

  return (
    <main className="legacy-page">
      <section className="legacy-featured-banner">
        <span className="legacy-pill">{commonT("featured")}</span>
        <h1>{t("title")}</h1>
        <p>
          {featured
            ? t("featuredChallenge", {
                number: featured.challenge_number,
                title: featured.title,
              })
            : t("emptyFeatured")}
        </p>
        {featured ? (
          <Link
            className="legacy-primary-button"
            href={`/coding/problem/${featured.id}`}
            style={{ marginTop: 24 }}
          >
            {commonT("challengeNow")}
          </Link>
        ) : null}
      </section>
      <CategoryToolbar
        difficultyLabel={t("difficulty")}
        recentLabel={t("recent")}
        searchPlaceholder={t("searchPlaceholder")}
      />
      <section className="legacy-challenge-grid">
        {challenges.map((challenge) => (
          <ChallengeCard challenge={challenge} key={challenge.id} />
        ))}
      </section>
    </main>
  );
}

function CategoryToolbar({
  difficultyLabel,
  recentLabel,
  searchPlaceholder,
}: {
  difficultyLabel: string;
  recentLabel: string;
  searchPlaceholder: string;
}): React.ReactElement {
  return (
    <div className="legacy-toolbar">
      <input
        className="legacy-search"
        placeholder={searchPlaceholder}
        readOnly
      />
      <div className="legacy-filter-group">
        <button className="legacy-filter-button active" type="button">
          {difficultyLabel}
        </button>
        <button className="legacy-filter-button" type="button">
          {recentLabel}
        </button>
      </div>
    </div>
  );
}
