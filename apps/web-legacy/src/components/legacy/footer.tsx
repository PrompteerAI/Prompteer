// Footer mirrors the compact legacy app footer.
import { Link } from "@/i18n/navigation";

export function LegacyFooter(): React.ReactElement {
  return (
    <footer className="legacy-footer">
      <div>
        <strong>PROMPTeer</strong>
        <p>Prompt challenge and sharing platform.</p>
      </div>
      <div className="legacy-footer-links">
        <a href="mailto:no-reply@prompteer.dev">Contact</a>
        <Link href="/settings">Settings</Link>
        <span>Copyright (c) 2026 hyuk and contributors</span>
      </div>
    </footer>
  );
}
