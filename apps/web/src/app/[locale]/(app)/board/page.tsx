// Community board page for seeded questions and public prompt shares.
import { ArrowRight, MessageSquareText, Sparkles } from "lucide-react";
import { getTranslations } from "next-intl/server";

import { ApiUnavailable } from "@/components/system/api-unavailable";
import { Link } from "@/i18n/navigation";
import { createPrompteerApiClient, unwrapApiResponse } from "@/lib/api-client";
import { normalizeError } from "@/lib/errors";
import type { components } from "@prompteer/shared-types";

export const dynamic = "force-dynamic";

const boardFeedLimit = 5;

type BoardFeed = components["schemas"]["BoardFeedRead"];

export default async function BoardPage(): Promise<React.ReactElement> {
  const t = await getTranslations("board");
  const errors = await getTranslations("errors");
  const api = createPrompteerApiClient();
  let feed: BoardFeed;

  try {
    feed = unwrapApiResponse(
      await api.GET("/api/v1/community/board", {
        params: { query: { limit: boardFeedLimit } },
        cache: "no-store",
      }),
    );
  } catch (error) {
    const normalizedError = await normalizeError(error);
    return (
      <main className="min-h-screen bg-zinc-50 px-6 py-8 text-zinc-950">
        <div className="mx-auto max-w-6xl">
          <ApiUnavailable
            actionLabel={errors("reload")}
            description={errors("apiUnavailableDescription")}
            error={normalizedError}
            requestIdLabel={errors("requestId")}
            title={errors("apiUnavailableTitle")}
          />
        </div>
      </main>
    );
  }

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
                <Link
                  aria-label={t("openPost", { title: post.title })}
                  className="group rounded-lg border border-zinc-200 bg-white p-5 shadow-sm transition hover:border-emerald-300 hover:shadow-md focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-emerald-700"
                  href={`/board/posts/${post.id}`}
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
                    {excerpt(post.content) ?? t("emptyContent")}
                  </p>
                  {post.challenge ? (
                    <p className="mt-4 text-xs font-medium uppercase text-emerald-700">
                      {t("challengePrefix", {
                        number: post.challenge.challenge_number,
                      })}{" "}
                      {post.challenge.title}
                    </p>
                  ) : null}
                  <span className="mt-4 inline-flex items-center gap-1 text-sm font-medium text-emerald-700">
                    {t("readMore")}
                    <ArrowRight
                      aria-hidden="true"
                      className="h-4 w-4 transition group-hover:translate-x-0.5"
                    />
                  </span>
                </Link>
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
                <Link
                  aria-label={t("openShare", {
                    title: share.challenge.title,
                  })}
                  className="group rounded-lg border border-zinc-200 bg-white p-5 shadow-sm transition hover:border-emerald-300 hover:shadow-md focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-emerald-700"
                  href={`/board/shares/${share.id}`}
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
                    {excerpt(share.prompt) ?? t("emptyContent")}
                  </p>
                  <p className="mt-4 text-xs font-medium uppercase text-emerald-700">
                    {t("challengeLabel", {
                      number: share.challenge.challenge_number,
                    })}
                  </p>
                  <span className="mt-4 inline-flex items-center gap-1 text-sm font-medium text-emerald-700">
                    {t("readMore")}
                    <ArrowRight
                      aria-hidden="true"
                      className="h-4 w-4 transition group-hover:translate-x-0.5"
                    />
                  </span>
                </Link>
              ))}
            </div>
          </div>
        </section>
      </div>
    </main>
  );
}

function excerpt(value: string | null): string | null {
  if (!value) {
    return null;
  }
  return value.length > 220 ? `${value.slice(0, 217)}...` : value;
}
