import { ChallengeCard } from "@/components/legacy/challenge-card";
import { Link } from "@/i18n/navigation";
import { readChallenges } from "@/lib/data";

export const dynamic = "force-dynamic";

export default async function ImageCategoryPage(): Promise<React.ReactElement> {
  const challenges = await readChallenges("img");
  const featured = challenges[0];

  return (
    <main className="legacy-page">
      <section className="legacy-featured-banner">
        <span className="legacy-pill">Featured</span>
        <h1>Image Challenges</h1>
        <p>
          Visual prompt practice with the rebuilt challenge API and
          deterministic feedback.
        </p>
        {featured ? (
          <Link
            className="legacy-primary-button"
            href={`/image/challenge/${featured.id}`}
            style={{ marginTop: 24 }}
          >
            Challenge now
          </Link>
        ) : null}
      </section>
      <div className="legacy-toolbar">
        <input
          className="legacy-search"
          placeholder="Search image challenges"
          readOnly
        />
        <div className="legacy-filter-group">
          <button className="legacy-filter-button active" type="button">
            Image
          </button>
          <Link className="legacy-filter-button" href="/category/video">
            Video
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
