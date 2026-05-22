// End-to-end checks that provider-compatible mock APIs are reachable through
// the default Compose nginx origin, not only through direct API dev ports.
import { expect, test } from "@playwright/test";

test("compose origin exposes provider-compatible mock endpoints", async ({
  request,
}) => {
  const chat = await request.post("/v1/chat/completions", {
    data: {
      model: "gpt-4.1-mini",
      messages: [{ role: "user", content: "Draft a concise prompt." }],
    },
  });
  expect(chat.status()).toBe(200);
  await expect(chat.json()).resolves.toMatchObject({
    object: "chat.completion",
    choices: [{ message: { role: "assistant" } }],
  });

  const message = await request.post("/v1/messages", {
    data: {
      model: "claude-sonnet-4-20250514",
      max_tokens: 64,
      messages: [{ role: "user", content: "Draft a concise prompt." }],
    },
  });
  expect(message.status()).toBe(200);
  await expect(message.json()).resolves.toMatchObject({
    type: "message",
    role: "assistant",
    content: [{ type: "text" }],
  });

  const checkout = await request.post("/v1/checkout/sessions", {
    form: {
      mode: "payment",
      success_url: "http://localhost/en/billing/success",
      cancel_url: "http://localhost/en/billing",
      customer_email: "free@prompteer.dev",
      "line_items[0][quantity]": "1",
      "line_items[0][price_data][currency]": "usd",
      "line_items[0][price_data][unit_amount]": "900",
      "line_items[0][price_data][product_data][name]": "Prompt credits",
    },
  });
  expect(checkout.status()).toBe(200);
  const checkoutBody = (await checkout.json()) as { id?: string };
  expect(checkoutBody.id).toMatch(/^cs_test_/);

  const email = await request.post("/v3/mail/send", {
    data: {
      personalizations: [{ to: [{ email: "free@prompteer.dev" }] }],
      from: { email: "no-reply@prompteer.dev" },
      subject: "Provider mock origin smoke",
      content: [
        {
          type: "text/plain",
          value:
            "The public Compose origin routed this SendGrid-shaped request.",
        },
      ],
    },
  });
  expect(email.status()).toBe(202);
});
