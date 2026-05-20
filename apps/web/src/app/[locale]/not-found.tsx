// Localized 404 page for routes under the active locale segment.
import { getTranslations } from "next-intl/server";

export default async function NotFoundPage(): Promise<React.ReactElement> {
  const t = await getTranslations("notFound");

  return (
    <main className="grid min-h-screen place-items-center bg-zinc-50 px-6">
      <h1 className="text-2xl font-semibold text-zinc-950">{t("title")}</h1>
    </main>
  );
}
