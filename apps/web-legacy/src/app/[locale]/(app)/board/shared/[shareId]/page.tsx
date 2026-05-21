import { Link } from "@/i18n/navigation";

type Props = {
  params: Promise<{ shareId: string }>;
};

export default async function SharedPostPage({
  params,
}: Props): Promise<React.ReactElement> {
  const { shareId } = await params;
  return (
    <main className="legacy-page">
      <section className="legacy-board">
        <div className="legacy-section-banner compact">
          <h1>Shared prompt</h1>
          <p>Shared prompt detail shell for legacy route {shareId}.</p>
        </div>
        <article className="legacy-panel">
          <h2>Prompt share detail API pending</h2>
          <p>
            Public shares appear on the board feed. Dedicated share detail
            routes will be wired when the API exposes them.
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
