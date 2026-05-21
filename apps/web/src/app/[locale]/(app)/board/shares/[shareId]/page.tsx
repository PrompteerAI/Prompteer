// Read-only community share detail page backed by the FastAPI detail endpoint.
import { ArrowLeft, CalendarDays, Hash, Sparkles } from "lucide-react";
import { notFound } from "next/navigation";
import { getTranslations } from "next-intl/server";

import { ApiUnavailable } from "@/components/system/api-unavailable";
import { Link } from "@/i18n/navigation";
import { createPrompteerApiClient, unwrapApiResponse } from "@/lib/api-client";
import { normalizeError } from "@/lib/errors";
import type { components } from "@prompteer/shared-types";

type ShareRead = components["schemas"]["ShareRead"];

type Props = {
  params: Promise<{ locale: string; shareId: string }>;
};

export const dynamic = "force-dynamic";

export default async function BoardShareDetailPage({
  params,
}: Props): Promise<React.ReactElement> {
  const [{ locale, shareId }, t, boardT, errors] = await Promise.all([
    params,
    getTranslations("board.detail"),
    getTranslations("board"),
    getTranslations("errors"),
  ]);
  const api = createPrompteerApiClient();
  let share: ShareRead;

  try {
    share = unwrapApiResponse(
      await api.GET("/api/v1/community/shares/{share_id}", {
        cache: "no-store",
        params: { path: { share_id: shareId } },
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
        <Link
          className="inline-flex min-h-10 items-center gap-2 rounded-md border border-zinc-300 px-3 text-sm font-medium text-zinc-900 transition hover:bg-white"
          href="/board"
        >
          <ArrowLeft aria-hidden="true" className="h-4 w-4" />
          {t("back")}
        </Link>

        <section className="mt-6 rounded-lg border border-zinc-200 bg-white p-6 shadow-sm">
          <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
            <div>
              <p className="inline-flex items-center gap-2 text-sm font-semibold uppercase text-emerald-700">
                <Sparkles aria-hidden="true" className="h-4 w-4" />
                {t("shareEyebrow")}
              </p>
              <h1 className="mt-3 text-3xl font-semibold tracking-normal text-zinc-950">
                {share.challenge.title}
              </h1>
            </div>
            <span className="w-fit rounded-md border border-zinc-200 px-2 py-1 text-xs font-medium uppercase text-zinc-700">
              {share.challenge.tag}
            </span>
          </div>

          <dl className="mt-6 grid gap-3 border-y border-zinc-200 py-4 text-sm sm:grid-cols-3">
            <div>
              <dt className="text-zinc-500">{t("author")}</dt>
              <dd className="mt-1 font-medium text-zinc-950">
                {share.author.display_name}
              </dd>
            </div>
            <div>
              <dt className="flex items-center gap-1 text-zinc-500">
                <CalendarDays aria-hidden="true" className="h-4 w-4" />
                {t("createdAt")}
              </dt>
              <dd className="mt-1 font-medium text-zinc-950">
                {formatDate(share.created_at, locale)}
              </dd>
            </div>
            <div>
              <dt className="flex items-center gap-1 text-zinc-500">
                <Hash aria-hidden="true" className="h-4 w-4" />
                {t("visibility")}
              </dt>
              <dd className="mt-1 font-medium text-zinc-950">
                {share.is_public ? t("public") : t("private")}
              </dd>
            </div>
          </dl>

          <p className="mt-5 rounded-md bg-emerald-50 px-3 py-2 text-sm font-medium text-emerald-900">
            {boardT("challengeLabel", {
              number: share.challenge.challenge_number,
            })}
          </p>

          <div className="mt-6">
            <h2 className="text-sm font-semibold text-zinc-950">
              {t("prompt")}
            </h2>
            <pre className="mt-3 whitespace-pre-wrap rounded-lg border border-zinc-200 bg-zinc-950 p-4 font-mono text-sm leading-6 text-zinc-50">
              {share.prompt ?? t("emptyContent")}
            </pre>
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
