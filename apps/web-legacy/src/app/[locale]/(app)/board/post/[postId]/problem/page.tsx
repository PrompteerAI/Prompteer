import { Link } from "@/i18n/navigation";

type Props = {
  params: Promise<{ postId: string }>;
};

export default async function BoardPostProblemPage({
  params,
}: Props): Promise<React.ReactElement> {
  const { postId } = await params;
  return (
    <main className="legacy-page">
      <section className="legacy-board">
        <div className="legacy-section-banner compact">
          <h1>Problem detail</h1>
          <p>Problem detail shell for board post {postId}.</p>
        </div>
        <article className="legacy-panel">
          <p>
            Challenge problem pages are available from each category.
            Board-linked problem details need a dedicated board-detail API
            before they can show authoritative data.
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
