"use client";

// Localized route-level error boundary for recoverable rendering failures.
import { useTranslations } from "next-intl";

export default function ErrorPage({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}): React.ReactElement {
  const t = useTranslations("errors");

  return (
    <main className="grid min-h-screen place-items-center bg-zinc-50 px-6">
      <div className="w-full max-w-md rounded-lg border border-zinc-200 bg-white p-6">
        <h1 className="text-xl font-semibold text-zinc-950">{t("title")}</h1>
        <p className="mt-2 text-sm text-zinc-600">{error.message}</p>
        <button
          className="mt-4 rounded-md bg-zinc-950 px-4 py-2 text-sm text-white"
          onClick={reset}
        >
          {t("retry")}
        </button>
      </div>
    </main>
  );
}
