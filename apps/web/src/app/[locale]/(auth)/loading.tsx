export default function AuthLoading(): React.ReactElement {
  return (
    <main className="grid min-h-screen place-items-center bg-zinc-50 px-6">
      <section className="w-full max-w-md rounded-lg border border-zinc-200 bg-white p-6">
        <div className="h-8 w-32 animate-pulse rounded-md bg-zinc-200" />
        <div className="mt-4 h-4 w-full animate-pulse rounded-md bg-zinc-200" />
        <div className="mt-2 h-4 w-4/5 animate-pulse rounded-md bg-zinc-200" />
        <div className="mt-6 h-11 w-full animate-pulse rounded-md bg-zinc-200" />
      </section>
    </main>
  );
}
