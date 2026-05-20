import { getTranslations } from "next-intl/server";

export default async function LoginPage(): Promise<React.ReactElement> {
  const t = await getTranslations("login");

  return (
    <main className="grid min-h-screen place-items-center bg-zinc-50 px-6">
      <div className="w-full max-w-sm rounded-lg border border-zinc-200 bg-white p-6 shadow-sm">
        <h1 className="text-2xl font-semibold text-zinc-950">{t("title")}</h1>
        <button className="mt-6 w-full rounded-md bg-zinc-950 px-4 py-2 text-sm font-medium text-white">
          {t("mock")}
        </button>
      </div>
    </main>
  );
}
