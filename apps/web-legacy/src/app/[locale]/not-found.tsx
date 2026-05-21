// Legacy-preview localized not-found route.
import { Link } from "@/i18n/navigation";

export default function NotFoundPage(): React.ReactElement {
  return (
    <main className="legacy-page">
      <section className="legacy-empty-state">
        <h1>Page not found</h1>
        <p>This legacy preview route is not available yet.</p>
        <Link className="legacy-primary-button" href="/">
          Back home
        </Link>
      </section>
    </main>
  );
}
