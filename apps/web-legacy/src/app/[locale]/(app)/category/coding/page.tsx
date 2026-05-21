// Legacy-preview coding challenge category route.
import { ChallengeCard } from "@/components/legacy/challenge-card";
import { Link } from "@/i18n/navigation";
import { readChallenges } from "@/lib/data";

export const dynamic = "force-dynamic";

export default async function CodingCategoryPage(): Promise<React.ReactElement> {
  const challenges = await readChallenges("ps");
  const featured = challenges[0];

  return (
    <main className="legacy-page">
      <section className="legacy-featured-banner">
        <span className="legacy-pill">Featured</span>
        <h1>Algorithm Challenges</h1>
        <p>
          {featured
            ? `Challenge #${featured.challenge_number} ${featured.title}`
            : "Seed algorithm challenges to start."}
        </p>
        {featured ? (
          <Link
            className="legacy-primary-button"
            href={`/coding/problem/${featured.id}`}
            style={{ marginTop: 24 }}
          >
            Challenge now
          </Link>
        ) : null}
      </section>
      <CategoryToolbar />
      <section className="legacy-challenge-grid">
        {challenges.map((challenge) => (
          <ChallengeCard challenge={challenge} key={challenge.id} />
        ))}
      </section>
    </main>
  );
}

function CategoryToolbar(): React.ReactElement {
  return (
    <div className="legacy-toolbar">
      <input
        className="legacy-search"
        placeholder="Search challenges"
        readOnly
      />
      <div className="legacy-filter-group">
        <button className="legacy-filter-button active" type="button">
          Difficulty
        </button>
        <button className="legacy-filter-button" type="button">
          Recent
        </button>
      </div>
    </div>
  );
}
