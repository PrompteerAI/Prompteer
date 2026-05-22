// Server-side renderer for the dev-only mock mailbox HTML pages. It reads
// captured emails through the FastAPI dev mailbox endpoints.
import { defaultLocalePath } from "@/i18n/paths";
import { getServerEnv } from "@/lib/env";
import enMessages from "@/messages/en.json";

const copy = enMessages.devMailbox;

interface MailboxMessage {
  id: string;
  path: string;
  to: string;
  from: string;
  subject: string;
}

interface MailboxListResponse {
  messages: MailboxMessage[];
}

interface MailboxMessageResponse extends MailboxMessage {
  raw: string;
}

export async function listMailboxMessages(): Promise<MailboxMessage[]> {
  const response = await apiGet<MailboxListResponse>("/dev/mailbox");
  return response.messages;
}

export async function readMailboxMessage(
  messageId: string,
): Promise<MailboxMessageResponse> {
  return apiGet<MailboxMessageResponse>(
    `/dev/mailbox/${encodeURIComponent(messageId)}`,
  );
}

export function mailboxIndexHtml(messages: MailboxMessage[]): string {
  const rows = messages
    .map(
      (message) => `
        <tr>
          <td data-label="Subject"><a href="/dev/mailbox/${encodeURIComponent(message.id)}">${escapeHtml(message.subject)}</a></td>
          <td data-label="To">${escapeHtml(message.to)}</td>
          <td data-label="From">${escapeHtml(message.from)}</td>
          <td data-label="Message"><code>${escapeHtml(message.id)}</code></td>
        </tr>`,
    )
    .join("");

  return shell(
    copy.title,
    `
      <header class="page-header">
        <div>
          <p>${copy.brand}</p>
          <h1>${copy.heading}</h1>
        </div>
        <a class="button" href="${defaultLocalePath("/")}">${copy.openApp}</a>
      </header>
      <section class="panel">
        <table>
          <thead>
            <tr>
              <th>${copy.subject}</th>
              <th>${copy.to}</th>
              <th>${copy.from}</th>
              <th>${copy.message}</th>
            </tr>
          </thead>
          <tbody>
            ${
              rows ||
              `<tr class="empty-row"><td colspan="4" class="empty">${copy.empty}</td></tr>`
            }
          </tbody>
        </table>
      </section>`,
  );
}

export function mailboxMessageHtml(message: MailboxMessageResponse): string {
  return shell(
    message.subject,
    `
      <header class="page-header">
        <div>
          <p>${copy.heading}</p>
          <h1>${escapeHtml(message.subject)}</h1>
        </div>
        <a class="button" href="/dev/mailbox">${copy.back}</a>
      </header>
      <section class="panel message-meta">
        <dl>
          <div><dt>${copy.to}</dt><dd>${escapeHtml(message.to)}</dd></div>
          <div><dt>${copy.from}</dt><dd>${escapeHtml(message.from)}</dd></div>
          <div><dt>${copy.message}</dt><dd><code>${escapeHtml(message.id)}</code></dd></div>
        </dl>
      </section>
      <section class="panel">
        <pre>${escapeHtml(message.raw)}</pre>
      </section>`,
  );
}

export function mailboxErrorHtml(status: number, detail: string): string {
  return shell(
    copy.unavailableTitle,
    `
      <header class="page-header">
        <div>
          <p>${copy.brand}</p>
          <h1>${copy.unavailableTitle}</h1>
        </div>
        <a class="button" href="${defaultLocalePath("/")}">${copy.openApp}</a>
      </header>
      <section class="panel error">
        <strong>${status}</strong>
        <span>${escapeHtml(detail)}</span>
      </section>`,
  );
}

export function htmlResponse(html: string, status = 200): Response {
  return new Response(html, {
    status,
    headers: {
      "content-type": "text/html; charset=utf-8",
      "cache-control": "no-store",
    },
  });
}

async function apiGet<T>(path: string): Promise<T> {
  const response = await fetch(`${apiBaseUrl()}${path}`, {
    headers: { accept: "application/json" },
    cache: "no-store",
  });
  if (!response.ok) {
    throw new Error(`API returned ${response.status}`);
  }
  return (await response.json()) as T;
}

function apiBaseUrl(): string {
  const serverEnv = getServerEnv();
  return (serverEnv.API_INTERNAL_URL || serverEnv.NEXT_PUBLIC_API_URL).replace(
    /\/+$/,
    "",
  );
}

function shell(title: string, body: string): string {
  return `<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>${escapeHtml(title)} - Prompteer</title>
    <style>
      :root {
        color-scheme: light;
        font-family:
          Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont,
          "Segoe UI", sans-serif;
        background: #f4f4f5;
        color: #18181b;
      }
      * {
        box-sizing: border-box;
      }
      body {
        margin: 0;
        min-height: 100vh;
        background: #f4f4f5;
      }
      main {
        width: min(1120px, calc(100vw - 48px));
        margin: 0 auto;
        padding: 40px 0;
      }
      .page-header {
        display: flex;
        align-items: flex-start;
        justify-content: space-between;
        gap: 24px;
        margin-bottom: 24px;
      }
      .page-header p {
        margin: 0 0 10px;
        color: #047857;
        font-size: 13px;
        font-weight: 700;
        letter-spacing: 0;
        text-transform: uppercase;
      }
      h1 {
        margin: 0;
        font-size: 38px;
        line-height: 1.15;
        font-weight: 680;
      }
      .button {
        display: inline-flex;
        align-items: center;
        height: 40px;
        padding: 0 14px;
        border: 1px solid #d4d4d8;
        border-radius: 6px;
        color: #18181b;
        font-size: 14px;
        font-weight: 600;
        text-decoration: none;
        background: #ffffff;
      }
      .panel {
        overflow: hidden;
        border: 1px solid #e4e4e7;
        border-radius: 8px;
        background: #ffffff;
        box-shadow: 0 1px 2px rgb(24 24 27 / 0.04);
      }
      table {
        width: 100%;
        border-collapse: collapse;
        font-size: 14px;
      }
      th,
      td {
        padding: 15px 16px;
        border-bottom: 1px solid #e4e4e7;
        text-align: left;
        vertical-align: top;
      }
      th {
        color: #52525b;
        font-size: 12px;
        font-weight: 700;
        text-transform: uppercase;
      }
      tr:last-child td {
        border-bottom: 0;
      }
      a {
        color: #065f46;
        font-weight: 650;
      }
      code {
        font-family: "SFMono-Regular", Consolas, "Liberation Mono", monospace;
        font-size: 12px;
        color: #3f3f46;
      }
      .empty {
        color: #71717a;
      }
      .message-meta {
        margin-bottom: 18px;
        padding: 18px;
      }
      dl {
        display: grid;
        gap: 14px;
        margin: 0;
      }
      dt {
        color: #71717a;
        font-size: 12px;
        font-weight: 700;
        text-transform: uppercase;
      }
      dd {
        margin: 4px 0 0;
        font-size: 14px;
      }
      pre {
        margin: 0;
        overflow: auto;
        padding: 18px;
        white-space: pre-wrap;
        word-break: break-word;
        font-family: "SFMono-Regular", Consolas, "Liberation Mono", monospace;
        font-size: 13px;
        line-height: 1.6;
      }
      .error {
        display: flex;
        gap: 12px;
        padding: 18px;
        color: #991b1b;
      }
      @media (max-width: 760px) {
        main {
          width: min(100vw - 28px, 1120px);
          padding: 24px 0;
        }
        .page-header {
          flex-direction: column;
        }
        h1 {
          font-size: 30px;
        }
        table,
        thead,
        tbody,
        tr,
        td {
          display: block;
        }
        thead {
          position: absolute;
          width: 1px;
          height: 1px;
          overflow: hidden;
          clip: rect(0 0 0 0);
          white-space: nowrap;
        }
        tbody {
          display: grid;
          gap: 12px;
          padding: 12px;
        }
        tr {
          border: 1px solid #e4e4e7;
          border-radius: 6px;
          padding: 14px;
        }
        tr:last-child td {
          border-bottom: 1px solid #e4e4e7;
        }
        td {
          display: grid;
          grid-template-columns: 78px minmax(0, 1fr);
          gap: 12px;
          padding: 10px 0;
          border-bottom: 1px solid #e4e4e7;
          overflow-wrap: anywhere;
        }
        td:first-child {
          padding-top: 0;
        }
        td:last-child {
          padding-bottom: 0;
          border-bottom: 0;
        }
        td::before {
          content: attr(data-label);
          color: #71717a;
          font-size: 12px;
          font-weight: 700;
          text-transform: uppercase;
        }
        .empty-row {
          padding: 0;
          border: 0;
        }
        .empty-row td {
          display: block;
          padding: 4px;
          border: 0;
        }
        .empty-row td::before {
          content: none;
        }
      }
    </style>
  </head>
  <body>
    <main>${body}</main>
  </body>
</html>`;
}

function escapeHtml(value: string): string {
  return value
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}
