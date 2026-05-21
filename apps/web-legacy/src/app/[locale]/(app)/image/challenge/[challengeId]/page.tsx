import { LegacyChallengeRunner } from "@/components/legacy/challenge-runner";
import { readGatewaySession } from "@/lib/auth-gateway";
import { readChallenge, readFeatures } from "@/lib/data";

export const dynamic = "force-dynamic";

type Props = {
  params: Promise<{ challengeId: string; locale: string }>;
};

export default async function ImageProblemPage({
  params,
}: Props): Promise<React.ReactElement> {
  const { challengeId, locale } = await params;
  const [challenge, features, session] = await Promise.all([
    readChallenge(challengeId),
    readFeatures(),
    readGatewaySession(),
  ]);

  return (
    <LegacyChallengeRunner
      challenge={challenge}
      demoLoginHref={`/dev/login-as/admin%40prompteer.dev?locale=${locale}`}
      isAuthenticated={Boolean(session?.user)}
      llmEnabled={features.llm}
      loginHref={`/${locale}/login`}
    />
  );
}
