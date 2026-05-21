"use client";

export default function ErrorPage({
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}): React.ReactElement {
  return (
    <main className="legacy-page">
      <section className="legacy-empty-state">
        <h1>Something went wrong</h1>
        <p>The legacy preview could not render this page.</p>
        <button className="legacy-primary-button" onClick={reset} type="button">
          Retry
        </button>
      </section>
    </main>
  );
}
