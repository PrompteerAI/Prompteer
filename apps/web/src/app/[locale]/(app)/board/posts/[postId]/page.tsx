// Read-only community post detail page backed by the FastAPI detail endpoint.
import { ArrowLeft, CalendarDays, Hash, MessageSquareText } from "lucide-react";
import { notFound } from "next/navigation";
import { getTranslations } from "next-intl/server";

import { ApiUnavailable } from "@/components/system/api-unavailable";
import { localizedPath } from "@/i18n/paths";
import { createPrompteerApiClient, unwrapApiResponse } from "@/lib/api-client";
import { normalizeError } from "@/lib/errors";
import type { components } from "@prompteer/shared-types";

type PostRead = components["schemas"]["PostRead"];

type Props = {
  params: Promise<{ locale: string; postId: string }>;
};

export const dynamic = "force-dynamic";

export default async function BoardPostDetailPage({
  params,
}: Props): Promise<React.ReactElement> {
  const [{ locale, postId }, t, boardT, errors] = await Promise.all([
    params,
    getTranslations("board.detail"),
    getTranslations("board"),
    getTranslations("errors"),
  ]);
  const api = createPrompteerApiClient();
  let post: PostRead;

  try {
    post = unwrapApiResponse(
      await api.GET("/api/v1/community/posts/{post_id}", {
        cache: "no-store",
        params: { path: { post_id: postId } },
      }),
    );
  } catch (error) {
    const normalizedError = await normalizeError(error);
    if (normalizedError.status === 404) {
      notFound();
    }
    return (
      <main className="min-h-screen bg-zinc-50 px-6 py-8 text-zinc-950">
        <div className="mx-auto max-w-4xl">
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
      <article className="mx-auto max-w-4xl">
        <a
          className="inline-flex min-h-10 items-center gap-2 rounded-md border border-zinc-300 px-3 text-sm font-medium text-zinc-900 transition hover:bg-white"
          href={localizedPath("/board", locale)}
        >
          <ArrowLeft aria-hidden="true" className="h-4 w-4" />
          {t("back")}
        </a>

        <section className="mt-6 rounded-lg border border-zinc-200 bg-white p-6 shadow-sm">
          <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
            <div>
              <p className="inline-flex items-center gap-2 text-sm font-semibold uppercase text-emerald-700">
                <MessageSquareText aria-hidden="true" className="h-4 w-4" />
                {t("postEyebrow")}
              </p>
              <h1 className="mt-3 text-3xl font-semibold tracking-normal text-zinc-950">
                {post.title}
              </h1>
            </div>
            <span className="w-fit rounded-md border border-zinc-200 px-2 py-1 text-xs font-medium capitalize text-zinc-700">
              {post.type}
            </span>
          </div>

          <dl className="mt-6 grid gap-3 border-y border-zinc-200 py-4 text-sm sm:grid-cols-3">
            <div>
              <dt className="text-zinc-500">{t("author")}</dt>
              <dd className="mt-1 font-medium text-zinc-950">
                {post.author.display_name}
              </dd>
            </div>
            <div>
              <dt className="flex items-center gap-1 text-zinc-500">
                <CalendarDays aria-hidden="true" className="h-4 w-4" />
                {t("createdAt")}
              </dt>
              <dd className="mt-1 font-medium text-zinc-950">
                {formatDate(post.created_at, locale)}
              </dd>
            </div>
            <div>
              <dt className="flex items-center gap-1 text-zinc-500">
                <Hash aria-hidden="true" className="h-4 w-4" />
                {t("tag")}
              </dt>
              <dd className="mt-1 font-medium uppercase text-zinc-950">
                {post.tag}
              </dd>
            </div>
          </dl>

          {post.challenge ? (
            <p className="mt-5 rounded-md bg-emerald-50 px-3 py-2 text-sm font-medium text-emerald-900">
              {boardT("challengePrefix", {
                number: post.challenge.challenge_number,
              })}{" "}
              {post.challenge.title}
            </p>
          ) : null}

          <div className="mt-6 whitespace-pre-wrap text-sm leading-7 text-zinc-700">
            {post.content ?? t("emptyContent")}
          </div>
        </section>
      </article>
    </main>
  );
}

function formatDate(value: string, locale: string): string {
  return new Intl.DateTimeFormat(locale, {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}
