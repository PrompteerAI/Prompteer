// Development-only seeded-user login route for Playwright and local demos.
import { defaultLocalePath } from "@/i18n/paths";
import { getSeedUser, seedLoginEnabled, signIn } from "@/lib/auth";

interface DevLoginAsRouteContext {
  params: Promise<{
    email: string;
  }>;
}

export async function GET(
  _request: Request,
  context: DevLoginAsRouteContext,
): Promise<Response> {
  const { email } = await context.params;
  const decodedEmail = decodeURIComponent(email).toLowerCase();
  if (!seedLoginEnabled() || !getSeedUser(decodedEmail)) {
    return new Response("Not found", { status: 404 });
  }

  await signIn("seed", {
    email: decodedEmail,
    redirectTo: defaultLocalePath("/"),
  });

  return new Response(null, { status: 204 });
}
