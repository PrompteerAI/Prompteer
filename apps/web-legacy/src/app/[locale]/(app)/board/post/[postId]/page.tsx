import { Link } from "@/i18n/navigation";
import { readBoard } from "@/lib/data";
import { findBoardPost, formatBoardDate } from "@/lib/legacy";

type Props = {
  params: Promise<{ postId: string }>;
};

export default async function BoardPostPage({
  params,
}: Props): Promise<React.ReactElement> {
  const { postId } = await params;
  const feed = await readBoard(50);
  const post = findBoardPost(feed, postId);

  if (!post) {
    return (
      <main className="legacy-page">
        <section className="legacy-board">
          <div className="legacy-empty-state">
            <h1>Post not found</h1>
            <p>
              This legacy board post is not in the current community feed. It
              may be older than the active feed window or no longer available.
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
          <h1>{post.title}</h1>
          <p>
            {post.type === "share" ? "Shared post" : "Question"} by{" "}
            {post.author.display_name} on {formatBoardDate(post.created_at)}.
          </p>
        </div>
        <article className="legacy-panel legacy-board-detail">
          <div className="legacy-detail-meta" aria-label="Post metadata">
            <span>Category: {post.tag.toUpperCase()}</span>
            <span>Type: {post.type}</span>
            <span>Author plan: {post.author.plan}</span>
          </div>
          <h2>Post</h2>
          <p className="legacy-detail-body">
            {post.content ?? "This post does not include additional body text."}
          </p>
          {post.challenge ? (
            <div className="legacy-detail-callout">
              <span>Problem {post.challenge.challenge_number}</span>
              <strong>{post.challenge.title}</strong>
              <p>
                {post.challenge.tag.toUpperCase()} / {post.challenge.level}
              </p>
            </div>
          ) : null}
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
