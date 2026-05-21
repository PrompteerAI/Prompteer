// Development mailbox index page backed by captured mock SendGrid messages.
import {
  htmlResponse,
  listMailboxMessages,
  mailboxErrorHtml,
  mailboxIndexHtml,
} from "@/server/dev-mailbox";
import { devRoutesEnabled } from "@/server/dev-routes";

export async function GET(): Promise<Response> {
  if (!devRoutesEnabled()) {
    return new Response("Not found", { status: 404 });
  }

  try {
    const messages = await listMailboxMessages();
    return htmlResponse(mailboxIndexHtml(messages));
  } catch (error) {
    return htmlResponse(mailboxErrorHtml(502, errorMessage(error)), 502);
  }
}

function errorMessage(error: unknown): string {
  return error instanceof Error ? error.message : "Mailbox API is unavailable.";
}
