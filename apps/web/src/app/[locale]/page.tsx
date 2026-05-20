import { ArrowRight, Code2, ImageIcon, Video } from "lucide-react";
import { getTranslations } from "next-intl/server";

const categories = [
  { key: "coding", icon: Code2, href: "/en/challenges/coding" },
  { key: "image", icon: ImageIcon, href: "/en/challenges/image" },
  { key: "video", icon: Video, href: "/en/challenges/video" }
] as const;

export default async function HomePage(): Promise<React.ReactElement> {
  const t = await getTranslations("home");

  return (
    <main className="min-h-screen bg-zinc-50 text-zinc-950">
      <section className="mx-auto flex min-h-screen w-full max-w-6xl flex-col justify-center px-6 py-10">
        <div className="max-w-3xl">
          <p className="text-sm font-semibold uppercase tracking-wide text-emerald-700">Prompteer</p>
          <h1 className="mt-4 text-5xl font-semibold leading-tight text-zinc-950">{t("title")}</h1>
          <p className="mt-5 max-w-2xl text-lg leading-8 text-zinc-650">{t("subtitle")}</p>
        </div>
        <div className="mt-10 grid gap-4 md:grid-cols-3">
          {categories.map((category) => {
            const Icon = category.icon;
            return (
              <a
                key={category.key}
                href={category.href}
                className="group rounded-lg border border-zinc-200 bg-white p-5 shadow-sm transition hover:border-emerald-500"
              >
                <Icon className="h-6 w-6 text-emerald-700" aria-hidden="true" />
                <div className="mt-5 flex items-center justify-between">
                  <h2 className="text-xl font-semibold">{t(category.key)}</h2>
                  <ArrowRight className="h-5 w-5 transition group-hover:translate-x-1" aria-hidden="true" />
                </div>
              </a>
            );
          })}
        </div>
      </section>
    </main>
  );
}
