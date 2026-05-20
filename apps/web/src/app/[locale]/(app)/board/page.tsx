// Community board page for seeded questions and public prompt shares.
import { MessageSquareText, Sparkles } from "lucide-react";
import { getTranslations } from "next-intl/server";

import { apiGet } from "@/lib/api-client";

export const dynamic = "force-dynamic";

interface BoardFeed {
  posts: BoardPost[];
  shares: BoardShare[];
}

interface Author {
  display_name: string;
  email: string;
  plan: string;
}

interface ChallengeSummary {
  challenge_number: number;
  tag: "ps" | "img" | "video";
  level: "easy" | "medium" | "hard";
  title: string;
}

interface BoardPost {
  id: string;
  type: "question" | "share";
  tag: "ps" | "img" | "video";
  title: string;
  content: string | null;
  author: Author;
  challenge: ChallengeSummary | null;
  created_at: string;
}

interface BoardShare {
  id: string;
  prompt: string | null;
  is_public: boolean;
  author: Author;
  challenge: ChallengeSummary;
  created_at: string;
}

export default async function BoardPage(): Promise<React.ReactElement> {
  const t = await getTranslations("board");
  const feed = await apiGet<BoardFeed>("/community/board", {
    cache: "no-store",
  });

  return (
    <main className="min-h-screen bg-zinc-50 px-6 py-8 text-zinc-950">
      <div className="mx-auto max-w-6xl">
        <div className="mb-6">
          <p className="text-sm font-semibold uppercase text-emerald-700">
            {t("eyebrow")}
          </p>
          <h1 className="mt-2 text-3xl font-semibold">{t("title")}</h1>
          <p className="mt-3 max-w-2xl text-sm leading-6 text-zinc-600">
            {t("description")}
          </p>
        </div>

        <section className="grid gap-6 lg:grid-cols-2">
          <div>
            <div className="mb-3 flex items-center gap-2 text-sm font-medium text-zinc-800">
              <MessageSquareText
                aria-hidden="true"
                className="h-4 w-4 text-emerald-700"
              />
              {t("questions")}
            </div>
            <div className="grid gap-3">
              {feed.posts.map((post) => (
                <article
                  className="rounded-lg border border-zinc-200 bg-white p-5 shadow-sm"
                  key={post.id}
                >
                  <div className="flex items-center justify-between gap-3">
                    <span className="rounded-md border border-zinc-200 px-2 py-1 text-xs font-medium capitalize text-zinc-700">
                      {post.type}
                    </span>
                    <span className="text-xs text-zinc-500">
                      {post.author.display_name}
                    </span>
                  </div>
                  <h2 className="mt-4 text-lg font-semibold text-zinc-950">
                    {post.title}
                  </h2>
                  <p className="mt-2 text-sm leading-6 text-zinc-600">
                    {post.content}
                  </p>
                  {post.challenge ? (
                    <p className="mt-4 text-xs font-medium uppercase text-emerald-700">
                      {t("challengePrefix", {
                        number: post.challenge.challenge_number,
                      })}{" "}
                      {post.challenge.title}
                    </p>
                  ) : null}
                </article>
              ))}
            </div>
          </div>

          <div>
            <div className="mb-3 flex items-center gap-2 text-sm font-medium text-zinc-800">
              <Sparkles
                aria-hidden="true"
                className="h-4 w-4 text-emerald-700"
              />
              {t("shares")}
            </div>
            <div className="grid gap-3">
              {feed.shares.map((share) => (
                <article
                  className="rounded-lg border border-zinc-200 bg-white p-5 shadow-sm"
                  key={share.id}
                >
                  <div className="flex items-center justify-between gap-3">
                    <span className="rounded-md border border-zinc-200 px-2 py-1 text-xs font-medium uppercase text-zinc-700">
                      {share.challenge.tag}
                    </span>
                    <span className="text-xs text-zinc-500">
                      {share.author.display_name}
                    </span>
                  </div>
                  <h2 className="mt-4 text-lg font-semibold text-zinc-950">
                    {share.challenge.title}
                  </h2>
                  <p className="mt-2 text-sm leading-6 text-zinc-600">
                    {share.prompt}
                  </p>
                  <p className="mt-4 text-xs font-medium uppercase text-emerald-700">
                    {t("challengeLabel", {
                      number: share.challenge.challenge_number,
                    })}
                  </p>
                </article>
              ))}
            </div>
          </div>
        </section>
      </div>
    </main>
  );
}
