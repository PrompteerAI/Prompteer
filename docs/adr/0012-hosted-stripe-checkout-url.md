# 0012 - Hosted Stripe Checkout URL

## Status

Accepted on 2026-05-20.

## Context

Prompteer creates Stripe Checkout Sessions on the FastAPI server. Stripe's Checkout Session API documents the hosted `url` as the redirect target for starting Checkout. The local mock also returns a Stripe-shaped session URL, but local development should keep the one-click mock completion path.

The repo previously documented a browser publishable key even though no frontend Stripe.js integration read it.

## Decision

Use the server-created Checkout Session `url` for real Stripe sessions. The Next.js billing screen shows an `Open Stripe Checkout` link when the provider is real Stripe, and it shows the local completion action only for mock sessions.

Remove the unused `NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY` from the documented environment contract. A browser publishable key will be introduced later only if Prompteer adopts Stripe.js or embedded Checkout.

## Consequences

Real checkout remains server-owned and keeps secret-key handling out of the browser. The local mock flow stays fully usable after `cp .env.example .env`, including in-app completion and mock webhook signing.

Future embedded Checkout work will need a separate frontend Stripe.js integration, public-key environment variable, and visual/e2e coverage for that browser path.

## Alternatives considered

Use Stripe.js `redirectToCheckout` with a publishable key and session id. That adds a browser SDK and public-key contract before the product needs it.

Keep the mock-only completion UI for all providers. That leaves real Stripe sessions created but not actionable from the web app.
