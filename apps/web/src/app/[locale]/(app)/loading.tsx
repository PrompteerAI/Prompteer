export default function AppLoading(): React.ReactElement {
  return (
    <main className="min-h-[calc(100vh-73px)] bg-zinc-50 px-6 py-8 text-zinc-950">
      <section className="mx-auto grid w-full max-w-6xl gap-5">
        <div className="flex items-center justify-between gap-4">
          <div className="h-8 w-44 animate-pulse rounded-md bg-zinc-200" />
          <div className="h-10 w-28 animate-pulse rounded-md bg-zinc-200" />
        </div>
        <div className="grid gap-4 lg:grid-cols-[260px_1fr]">
          <div className="h-80 animate-pulse rounded-lg border border-zinc-200 bg-white" />
          <div className="h-80 animate-pulse rounded-lg border border-zinc-200 bg-white" />
        </div>
      </section>
    </main>
  );
}
