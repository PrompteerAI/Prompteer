// Legacy-preview route for categories that are not yet available.
import { Clock3 } from "lucide-react";

import { Link } from "@/i18n/navigation";

export default function PreparingPage(): React.ReactElement {
  return (
    <main className="legacy-page">
      <section className="legacy-empty-state">
        <Clock3 aria-hidden="true" color="#1971c2" size={80} />
        <h1>Preparing</h1>
        <p>This legacy category shell is ready for future backend coverage.</p>
        <Link className="legacy-primary-button" href="/">
          Back home
        </Link>
      </section>
    </main>
  );
}
