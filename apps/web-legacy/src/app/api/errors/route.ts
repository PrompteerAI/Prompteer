// Client error report endpoint for legacy-preview error boundaries.
import { type NextRequest } from "next/server";
import { z } from "zod";

const errorReportSchema = z.object({
  message: z.string().max(500),
  digest: z.string().max(200).optional(),
  path: z.string().max(300),
  userAgent: z.string().max(300).optional(),
});

export async function POST(request: NextRequest): Promise<Response> {
  let body: unknown;
  try {
    body = await request.json();
  } catch {
    return invalidReportResponse();
  }

  const payload = errorReportSchema.safeParse(body);
  if (!payload.success) {
    return invalidReportResponse();
  }

  console.warn(
    JSON.stringify({
      event: "legacy_client_error_reported",
      request_id: request.headers.get("x-request-id"),
      ...payload.data,
    }),
  );

  return Response.json({ ok: true }, { status: 202 });
}

function invalidReportResponse(): Response {
  return Response.json(
    { ok: false, code: "invalid_error_report" },
    { status: 400 },
  );
}
