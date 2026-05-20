// Lightweight web process health endpoint used by container health checks.
export function GET(): Response {
  return Response.json({ status: "ok" });
}
