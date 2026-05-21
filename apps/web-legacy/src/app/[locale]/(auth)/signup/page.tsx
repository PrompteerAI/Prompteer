import { Link } from "@/i18n/navigation";

export default function SignupPage(): React.ReactElement {
  return (
    <main className="legacy-auth-screen">
      <section
        className="legacy-auth-card"
        style={{ width: "min(762px, 100%)" }}
      >
        <h1>Create account</h1>
        <p>
          Account creation is owned by the primary Auth.js app in the rebuilt
          architecture. Use demo login locally or configure real Google OAuth.
        </p>
        <div className="legacy-auth-actions">
          <Link className="legacy-primary-button" href="/login">
            Open demo login
          </Link>
          <Link className="legacy-secondary-button" href="/">
            Back home
          </Link>
        </div>
      </section>
    </main>
  );
}
