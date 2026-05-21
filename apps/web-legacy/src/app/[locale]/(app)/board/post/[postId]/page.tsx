import { Link } from "@/i18n/navigation";

type Props = {
  params: Promise<{ postId: string }>;
};

export default async function BoardPostPage({
  params,
}: Props): Promise<React.ReactElement> {
  const { postId } = await params;
  return (
    <main className="legacy-page">
      <section className="legacy-board">
        <div className="legacy-section-banner compact">
          <h1>Board post</h1>
          <p>Post detail shell for legacy route {postId}.</p>
        </div>
        <article className="legacy-panel">
          <h2>Community detail API pending</h2>
          <p>
            The board feed is live. Dedicated post detail endpoints are not part
            of the rebuilt public API yet, so this route keeps the legacy shape
            without inventing data.
          </p>
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
