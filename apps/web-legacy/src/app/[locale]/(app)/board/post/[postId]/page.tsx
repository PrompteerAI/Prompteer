import { Link } from "@/i18n/navigation";
import { ApiResponseError } from "@/lib/api-client";
import { readBoardPost, type Post } from "@/lib/data";
import { formatBoardDate } from "@/lib/legacy";

type Props = {
  params: Promise<{ postId: string }>;
};

export default async function BoardPostPage({
  params,
}: Props): Promise<React.ReactElement> {
  const { postId } = await params;
  const post = await readPostDetail(postId);

  if (!post) {
    return (
      <main className="legacy-page">
        <section className="legacy-board">
          <div className="legacy-empty-state">
            <h1>Post not found</h1>
            <p>
              This legacy board post is no longer available from the community
              detail API.
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

async function readPostDetail(postId: string): Promise<Post | null> {
  try {
    return await readBoardPost(postId);
  } catch (error) {
    if (error instanceof ApiResponseError && error.response.status === 404) {
      return null;
    }
    throw error;
  }
}
