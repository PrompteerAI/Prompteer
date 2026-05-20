// JWKS endpoint exposing the public key for API bearer token verification.
import { getAuthJwtPublicJwk } from "@/server/auth-jwt";

export function GET(): Response {
  return Response.json(
    { keys: [getAuthJwtPublicJwk()] },
    {
      headers: {
        "Cache-Control": "public, max-age=300",
      },
    },
  );
}
