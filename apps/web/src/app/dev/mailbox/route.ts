import {
  htmlResponse,
  listMailboxMessages,
  mailboxErrorHtml,
  mailboxIndexHtml,
} from "@/server/dev-mailbox";

export async function GET(): Promise<Response> {
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
