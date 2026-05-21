import { AlertTriangle, RefreshCw } from "lucide-react";

import type { NormalizedError } from "@/lib/errors";

type ApiUnavailableProps = {
  title: string;
  description: string;
  actionLabel: string;
  requestIdLabel: string;
  error: NormalizedError;
};

export function ApiUnavailable({
  title,
  description,
  actionLabel,
  requestIdLabel,
  error,
}: ApiUnavailableProps): React.ReactElement {
  const showDetail = process.env.NODE_ENV !== "production";

  return (
    <section className="rounded-lg border border-amber-200 bg-amber-50 p-6 text-amber-950">
      <div className="flex flex-col gap-5 sm:flex-row sm:items-start sm:justify-between">
        <div className="flex gap-3">
          <AlertTriangle
            aria-hidden="true"
            className="mt-1 h-5 w-5 shrink-0 text-amber-700"
          />
          <div>
            <h2 className="text-lg font-semibold">{title}</h2>
            <p className="mt-2 text-sm leading-6 text-amber-900">
              {description}
            </p>
            {showDetail ? (
              <p className="mt-3 text-sm leading-6 text-amber-900">
                {error.message}
              </p>
            ) : null}
            {error.requestId ? (
              <p className="mt-3 break-all font-mono text-xs text-amber-800">
                {requestIdLabel}: {error.requestId}
              </p>
            ) : null}
          </div>
        </div>
        <a
          className="inline-flex min-h-11 shrink-0 items-center justify-center gap-2 rounded-md border border-amber-300 bg-white px-4 text-sm font-medium text-amber-950 transition hover:bg-amber-100"
          href=""
        >
          <RefreshCw aria-hidden="true" className="h-4 w-4" />
          {actionLabel}
        </a>
      </div>
    </section>
  );
}
