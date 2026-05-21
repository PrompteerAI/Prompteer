import { Link } from "@/i18n/navigation";

export default function BoardWritePage(): React.ReactElement {
  return (
    <main className="legacy-page">
      <section className="legacy-board">
        <div className="legacy-section-banner compact">
          <h1>Write post</h1>
          <p>
            The legacy write surface is present; write APIs are not exposed yet.
          </p>
        </div>
        <form className="legacy-panel">
          <label>
            Title
            <input
              className="legacy-search"
              readOnly
              value="Legacy preview draft"
            />
          </label>
          <label style={{ display: "block", marginTop: 18 }}>
            Content
            <textarea
              className="legacy-prompt-area"
              readOnly
              value="Board creation will be wired once the rebuilt API exposes mutation endpoints for community posts."
            />
          </label>
          <Link
            className="legacy-secondary-button"
            href="/board"
            style={{ marginTop: 18 }}
          >
            Back to board
          </Link>
        </form>
      </section>
    </main>
  );
}
