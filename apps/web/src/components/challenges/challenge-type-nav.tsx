// Local navigation between challenge categories.
import { Code2, FileImage, FileVideo } from "lucide-react";

import { Link } from "@/i18n/navigation";

type ChallengeType = "coding" | "image" | "video";

type ChallengeTypeNavProps = {
  active: ChallengeType;
  labels: Record<ChallengeType, string>;
  navLabel: string;
};

const challengeTypeItems = [
  { key: "coding", href: "/challenges/coding", icon: Code2 },
  { key: "image", href: "/challenges/image", icon: FileImage },
  { key: "video", href: "/challenges/video", icon: FileVideo },
] as const;

export function ChallengeTypeNav({
  active,
  labels,
  navLabel,
}: ChallengeTypeNavProps): React.ReactElement {
  return (
    <nav aria-label={navLabel} className="mb-6 flex flex-wrap gap-2">
      {challengeTypeItems.map((item) => {
        const Icon = item.icon;
        const isActive = item.key === active;

        return (
          <Link
            aria-current={isActive ? "page" : undefined}
            className={
              isActive
                ? "inline-flex min-h-10 items-center gap-2 rounded-md bg-zinc-950 px-3 text-sm font-medium text-white"
                : "inline-flex min-h-10 items-center gap-2 rounded-md border border-zinc-200 bg-white px-3 text-sm font-medium text-zinc-700 transition hover:border-emerald-500 hover:text-zinc-950 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-zinc-950"
            }
            href={item.href}
            key={item.key}
          >
            <Icon aria-hidden="true" className="h-4 w-4" />
            {labels[item.key]}
          </Link>
        );
      })}
    </nav>
  );
}
