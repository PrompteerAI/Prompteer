import { LegacyChallengeRunner } from "@/components/legacy/challenge-runner";
import { readChallenge, readFeatures } from "@/lib/data";

export const dynamic = "force-dynamic";

type Props = {
  params: Promise<{ challengeId: string }>;
};

export default async function VideoProblemPage({
  params,
}: Props): Promise<React.ReactElement> {
  const { challengeId } = await params;
  const [challenge, features] = await Promise.all([
    readChallenge(challengeId),
    readFeatures(),
  ]);

  return (
    <LegacyChallengeRunner challenge={challenge} llmEnabled={features.llm} />
  );
}
