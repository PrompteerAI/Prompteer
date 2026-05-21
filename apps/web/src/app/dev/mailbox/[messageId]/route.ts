// Development mailbox detail page backed by captured mock SendGrid messages.
import {
  htmlResponse,
  mailboxErrorHtml,
  mailboxMessageHtml,
  readMailboxMessage,
} from "@/server/dev-mailbox";
import { devRoutesEnabled } from "@/server/dev-routes";

interface MailboxMessageRouteContext {
  params: Promise<{
    messageId: string;
  }>;
}

export async function GET(
  _request: Request,
  context: MailboxMessageRouteContext,
): Promise<Response> {
  if (!devRoutesEnabled()) {
    return new Response("Not found", { status: 404 });
  }

  const { messageId } = await context.params;
  try {
    const message = await readMailboxMessage(decodeURIComponent(messageId));
    return htmlResponse(mailboxMessageHtml(message));
  } catch (error) {
    return htmlResponse(mailboxErrorHtml(404, errorMessage(error)), 404);
  }
}

function errorMessage(error: unknown): string {
  return error instanceof Error ? error.message : "Message was not found.";
}
