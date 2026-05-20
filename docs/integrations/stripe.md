# Stripe Integration

Verified on: 2026-05-20

Sources:

- https://docs.stripe.com/keys
- https://docs.stripe.com/api/checkout/sessions
- https://docs.stripe.com/api/checkout/sessions/create
- https://docs.stripe.com/api/checkout/sessions/retrieve
- https://docs.stripe.com/api/checkout/sessions/expire
- https://docs.stripe.com/webhooks/signature

Prompteer uses `STRIPE_SECRET_KEY` and `STRIPE_WEBHOOK_SECRET` for real checkout. Empty values select local mock checkout sessions and mock webhook signing.

The frontend uses hosted Checkout by opening the `url` returned by a server-created Checkout Session. The current flow does not load Stripe.js or require a browser publishable key. If Prompteer later adopts embedded Checkout or Stripe.js `redirectToCheckout`, add that key and document the new browser contract separately.

## Local mock

The dev mock exposes the Stripe-shaped Checkout Session endpoints:

- `POST /v1/checkout/sessions`
- `GET /v1/checkout/sessions/:id`
- `POST /v1/checkout/sessions/:id/expire`
- `POST /api/v1/billing/checkout`
- `GET /api/v1/billing/checkout/:id`
- `POST /api/v1/billing/checkout/:id/complete`

It accepts JSON payloads and Stripe-style bracket form payloads such as `line_items[0][price_data][unit_amount]=1200`.

The mock Checkout Session response keeps the upstream fields the app needs for billing flows:

```json
{
  "id": "cs_test_<random>",
  "object": "checkout.session",
  "amount_subtotal": 1200,
  "amount_total": 1200,
  "currency": "usd",
  "mode": "subscription",
  "customer": null,
  "metadata": {
    "user_id": "00000000-0000-4000-8000-000000000002"
  },
  "payment_intent": null,
  "payment_status": "unpaid",
  "status": "open",
  "subscription": null,
  "success_url": "http://localhost:3000/en/billing/success",
  "cancel_url": "http://localhost:3000/en/billing",
  "url": "https://checkout.stripe.com/c/pay/cs_test_<random>#mock"
}
```

`GET /dev/stripe/complete?session_id=...` is dev-only. It marks an open mock session complete, sets `payment_status` to `paid`, creates a mock `payment_intent` or `subscription` depending on the session mode, and returns a `checkout.session.completed` event plus a mock `Stripe-Signature` header value.

`POST /api/v1/billing/checkout/:id/complete` is the product-facing local-dev wrapper used by the Next.js billing screen. It is available only when dev routes are enabled and no real `STRIPE_SECRET_KEY` is configured.

When a real Stripe session is created, the Next.js billing screen shows an `Open Stripe Checkout` link pointing at the returned hosted Checkout URL instead of showing the mock completion action.

Webhook signature verification follows Stripe's documented `t=timestamp,v1=signature` HMAC-SHA256 scheme. Empty `STRIPE_WEBHOOK_SECRET` uses the local-only `whsec_mock_prompteer` secret.
