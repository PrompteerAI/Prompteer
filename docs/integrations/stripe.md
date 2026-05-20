# Stripe Integration

Verified on: 2026-05-20

Sources:

- https://docs.stripe.com/keys
- https://docs.stripe.com/api

Prompteer uses `STRIPE_SECRET_KEY`, `NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY`, and `STRIPE_WEBHOOK_SECRET` for real checkout. Empty values select local mock checkout sessions and mock webhook signing.
