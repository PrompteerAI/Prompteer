import { ChallengeCard } from "@/components/legacy/challenge-card";
import { Link } from "@/i18n/navigation";
import { readChallenges } from "@/lib/data";

export const dynamic = "force-dynamic";

export default async function VideoCategoryPage(): Promise<React.ReactElement> {
  const challenges = await readChallenges("video");
  const featured = challenges[0];

  return (
    <main className="legacy-page">
      <section className="legacy-featured-banner">
        <span className="legacy-pill">Featured</span>
        <h1>Video Challenges</h1>
        <p>
          Motion and scene prompts use the same backend challenge runner while
          keeping the legacy video-card treatment.
        </p>
        {featured ? (
          <Link
            className="legacy-primary-button"
            href={`/video/challenge/${featured.id}`}
            style={{ marginTop: 24 }}
          >
            Challenge now
          </Link>
        ) : null}
      </section>
      <div className="legacy-toolbar">
        <input
          className="legacy-search"
          placeholder="Search video challenges"
          readOnly
        />
        <div className="legacy-filter-group">
          <Link className="legacy-filter-button" href="/category/image">
            Image
          </Link>
          <button className="legacy-filter-button active" type="button">
            Video
          </button>
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
