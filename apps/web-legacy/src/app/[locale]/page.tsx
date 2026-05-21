// Legacy-preview landing route modeled after the original frontend.
import { ImageIcon, TerminalSquare, Video } from "lucide-react";

import { ChallengeCard } from "@/components/legacy/challenge-card";
import { Link } from "@/i18n/navigation";
import { readChallenges } from "@/lib/data";

export const dynamic = "force-dynamic";

export default async function HomePage(): Promise<React.ReactElement> {
  const [coding, image, video] = await Promise.all([
    readChallenges("ps"),
    readChallenges("img"),
    readChallenges("video"),
  ]);
  const topChallenges = [coding[0], image[0], video[0]].filter(Boolean);

  return (
    <main className="legacy-main">
      <section className="legacy-section-banner">
        <h1>Top Challenges</h1>
        <p>
          Practice prompt design across algorithm, image, and video challenges
          using the rebuilt FastAPI backend.
        </p>
      </section>
      <section className="legacy-home-grid" aria-label="Top challenges">
        {topChallenges.map((challenge) => (
          <ChallengeCard
            challenge={challenge}
            key={challenge.id}
            variant="media"
          />
        ))}
      </section>

      <section className="legacy-section-banner compact">
        <h1>Challenge Category</h1>
      </section>
      <section
        className="legacy-category-grid"
        aria-label="Challenge categories"
      >
        <CategoryTile
          description="Algorithm prompts, solution reasoning, and output critique."
          href="/category/coding"
          icon={<TerminalSquare aria-hidden="true" size={32} />}
          title="Algorithm"
        />
        <CategoryTile
          description="Visual prompt structure with image-specific backend feedback."
          href="/category/image"
          icon={<ImageIcon aria-hidden="true" size={32} />}
          title="Image"
        />
        <CategoryTile
          description="Scene, motion, timing, and consistency prompt feedback."
          href="/category/video"
          icon={<Video aria-hidden="true" size={32} />}
          title="Video"
        />
        <CategoryTile
          description="Additional legacy categories are staged for future API coverage."
          href="/category/preparing"
          title="Preparing"
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
