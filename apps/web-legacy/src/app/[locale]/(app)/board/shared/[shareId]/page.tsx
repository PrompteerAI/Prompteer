// Legacy-preview shared prompt run detail route.
import { Link } from "@/i18n/navigation";
import { ApiResponseError } from "@/lib/api-client";
import { readBoardShare, type Share } from "@/lib/data";
import { formatBoardDate } from "@/lib/legacy";

type Props = {
  params: Promise<{ shareId: string }>;
};

export default async function SharedPostPage({
  params,
}: Props): Promise<React.ReactElement> {
  const { shareId } = await params;
  const share = await readShareDetail(shareId);

  if (!share) {
    return (
      <main className="legacy-page">
        <section className="legacy-board">
          <div className="legacy-empty-state">
            <h1>Shared prompt not found</h1>
            <p>
              This shared prompt may be private or no longer available from the
              community detail API.
            </p>
            <Link
              className="legacy-secondary-button"
              href="/board"
              style={{ marginTop: 18 }}
            >
              Back to board
            </Link>
          </div>
        </section>
      </main>
    );
  }

  return (
    <main className="legacy-page">
      <section className="legacy-board">
        <div className="legacy-section-banner compact">
          <h1>{share.challenge.title}</h1>
          <p>
            Shared by {share.author.display_name} on{" "}
            {formatBoardDate(share.created_at)}.
          </p>
        </div>
        <article className="legacy-panel legacy-board-detail">
          <div className="legacy-detail-meta" aria-label="Share metadata">
            <span>Category: {share.challenge.tag.toUpperCase()}</span>
            <span>Problem: {share.challenge.challenge_number}</span>
            <span>Author plan: {share.author.plan}</span>
          </div>
          <h2>Prompt</h2>
          <p className="legacy-detail-body">
            {share.prompt ?? "This shared run does not include prompt text."}
          </p>
          <div className="legacy-detail-callout">
            <span>Problem {share.challenge.challenge_number}</span>
            <strong>{share.challenge.title}</strong>
            <p>
              {share.challenge.tag.toUpperCase()} / {share.challenge.level}
            </p>
          </div>
          <Link
            className="legacy-secondary-button"
            href="/board"
            style={{ marginTop: 18 }}
          >
            Back to board
          </Link>
        </article>
      </section>
    </main>
  );
}

async function readShareDetail(shareId: string): Promise<Share | null> {
  try {
    return await readBoardShare(shareId);
  } catch (error) {
    if (error instanceof ApiResponseError && error.response.status === 404) {
      return null;
    }
    throw error;
  }
}
