# Stripe Integration

Verified on: 2026-05-20

Sources:

- https://docs.stripe.com/keys
- https://docs.stripe.com/api/checkout/sessions
- https://docs.stripe.com/api/checkout/sessions/create
- https://docs.stripe.com/api/checkout/sessions/retrieve
- https://docs.stripe.com/api/checkout/sessions/expire
- https://docs.stripe.com/webhooks/signature

Prompteer uses `STRIPE_SECRET_KEY`, `NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY`, and `STRIPE_WEBHOOK_SECRET` for real checkout. Empty values select local mock checkout sessions and mock webhook signing.

## Local mock

The dev mock exposes the Stripe-shaped Checkout Session endpoints:

- `POST /v1/checkout/sessions`
- `GET /v1/checkout/sessions/:id`
- `POST /v1/checkout/sessions/:id/expire`

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

Webhook signature verification follows Stripe's documented `t=timestamp,v1=signature` HMAC-SHA256 scheme. Empty `STRIPE_WEBHOOK_SECRET` uses the local-only `whsec_mock_prompteer` secret.
