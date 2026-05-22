export default function LocaleLoading(): React.ReactElement {
  return (
    <main className="min-h-screen bg-zinc-50 px-6 py-10 text-zinc-950">
      <section className="mx-auto grid w-full max-w-6xl gap-6">
        <div className="h-10 w-48 animate-pulse rounded-md bg-zinc-200" />
        <div className="grid gap-4 md:grid-cols-[1.4fr_0.8fr]">
          <div className="min-h-72 animate-pulse rounded-lg border border-zinc-200 bg-white" />
          <div className="min-h-72 animate-pulse rounded-lg border border-zinc-200 bg-white" />
        </div>
        <div className="grid gap-3 md:grid-cols-3">
          <div className="h-28 animate-pulse rounded-lg border border-zinc-200 bg-white" />
          <div className="h-28 animate-pulse rounded-lg border border-zinc-200 bg-white" />
          <div className="h-28 animate-pulse rounded-lg border border-zinc-200 bg-white" />
        </div>
      </section>
    </main>
  );
}
