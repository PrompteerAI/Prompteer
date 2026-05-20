import {
  CodingChallengeRunner,
  type Challenge,
} from "@/components/challenges/coding-challenge-runner";
import { apiGet } from "@/lib/api-client";

export const dynamic = "force-dynamic";

export default async function CodingChallengesPage(): Promise<React.ReactElement> {
  const challenges = await apiGet<Challenge[]>("/challenges?tag=ps", {
    cache: "no-store",
  });

  return (
    <main className="min-h-screen bg-zinc-50 px-6 py-8 text-zinc-950">
      <div className="mx-auto max-w-6xl">
        <div className="mb-6">
          <p className="text-sm font-semibold uppercase text-emerald-700">
            Coding
          </p>
          <h1 className="mt-2 text-3xl font-semibold">
            Prompt repair workspace
          </h1>
          <p className="mt-3 max-w-2xl text-sm leading-6 text-zinc-600">
            Pick a seeded coding challenge, draft a prompt, and run it through
            the local LLM mock.
          </p>
        </div>
        <CodingChallengeRunner challenges={challenges} />
      </div>
    </main>
  );
}
