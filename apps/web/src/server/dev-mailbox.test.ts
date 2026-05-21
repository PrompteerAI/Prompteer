// Unit tests for dev mailbox fetch helpers and escaped HTML rendering.
import { afterEach, describe, expect, it, vi } from "vitest";

import {
  htmlResponse,
  mailboxErrorHtml,
  mailboxIndexHtml,
  mailboxMessageHtml,
} from "./dev-mailbox";

afterEach(() => {
  vi.unstubAllGlobals();
  vi.unstubAllEnvs();
});

describe("dev-mailbox API helpers", () => {
  it("lists mailbox messages from the internal API without caching", async () => {
    vi.resetModules();
    const fetchMock = vi.fn().mockResolvedValue(
      Response.json({
        messages: [
          {
            id: "welcome.eml",
            path: ".mock/email/welcome.eml",
            to: "free@prompteer.dev",
            from: "hello@prompteer.dev",
            subject: "Welcome",
          },
        ],
      }),
    );
    vi.stubGlobal("fetch", fetchMock);
    vi.stubEnv("API_INTERNAL_URL", "http://api.internal/api/v1/");

    const { listMailboxMessages } = await import("./dev-mailbox");

    await expect(listMailboxMessages()).resolves.toEqual([
      expect.objectContaining({ id: "welcome.eml", subject: "Welcome" }),
    ]);
    expect(fetchMock).toHaveBeenCalledWith(
      "http://api.internal/api/v1/dev/mailbox",
      {
        headers: { accept: "application/json" },
        cache: "no-store",
      },
    );
  });

  it("URL-encodes message ids and falls back to the public API URL", async () => {
    vi.resetModules();
    const fetchMock = vi.fn().mockResolvedValue(
      Response.json({
        id: "id with spaces.eml",
        path: ".mock/email/id with spaces.eml",
        to: "paid@prompteer.dev",
        from: "billing@prompteer.dev",
        subject: "Receipt",
        raw: "Subject: Receipt",
      }),
    );
    vi.stubGlobal("fetch", fetchMock);
    vi.stubEnv("API_INTERNAL_URL", "");
    vi.stubEnv("NEXT_PUBLIC_API_URL", "http://localhost:8000/api/v1/");

    const { readMailboxMessage } = await import("./dev-mailbox");

    await expect(
      readMailboxMessage("id with spaces.eml"),
    ).resolves.toMatchObject({
      raw: "Subject: Receipt",
    });
    expect(fetchMock).toHaveBeenCalledWith(
      "http://localhost:8000/api/v1/dev/mailbox/id%20with%20spaces.eml",
      expect.any(Object),
    );
  });

  it("throws a concise error when the API returns a non-2xx response", async () => {
    vi.resetModules();
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(new Response("nope", { status: 503 })),
    );

    const { listMailboxMessages } = await import("./dev-mailbox");

    await expect(listMailboxMessages()).rejects.toThrow("API returned 503");
  });
});

describe("dev-mailbox HTML rendering", () => {
  it("escapes message fields in the index page", () => {
    const html = mailboxIndexHtml([
      {
        id: "msg <1>.eml",
        path: ".mock/email/msg.eml",
        to: "user<script>@example.com",
        from: "Prompteer & Co <hello@prompteer.dev>",
        subject: "Hello <Admin> & team",
      },
    ]);

    expect(html).toContain("Hello &lt;Admin&gt; &amp; team");
    expect(html).toContain("user&lt;script&gt;@example.com");
    expect(html).toContain("Prompteer &amp; Co &lt;hello@prompteer.dev&gt;");
    expect(html).toContain("/dev/mailbox/msg%20%3C1%3E.eml");
    expect(html).not.toContain("Hello <Admin>");
  });

  it("renders an empty-state row when no messages exist", () => {
    expect(mailboxIndexHtml([])).toContain("No captured messages yet.");
  });

  it("escapes raw email content and metadata on the message page", () => {
    const html = mailboxMessageHtml({
      id: "receipt.eml",
      path: ".mock/email/receipt.eml",
      to: "paid@prompteer.dev",
      from: "billing@prompteer.dev",
      subject: 'Receipt "May"',
      raw: "Subject: Receipt\n<script>alert('x')</script>",
    });

    expect(html).toContain("Receipt &quot;May&quot;");
    expect(html).toContain("&lt;script&gt;alert(&#39;x&#39;)&lt;/script&gt;");
    expect(html).not.toContain("<script>alert");
  });

  it("escapes detail in error pages and returns no-store HTML responses", async () => {
    const html = mailboxErrorHtml(503, "API <offline> & retry");
    const response = htmlResponse(html, 503);

    expect(html).toContain("API &lt;offline&gt; &amp; retry");
    expect(response.status).toBe(503);
    expect(response.headers.get("content-type")).toBe(
      "text/html; charset=utf-8",
    );
    expect(response.headers.get("cache-control")).toBe("no-store");
    await expect(response.text()).resolves.toBe(html);
  });

  it("uses the default 200 status for successful HTML responses", () => {
    const response = htmlResponse("<p>ok</p>");

    expect(response.status).toBe(200);
  });
});
