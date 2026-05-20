# SendGrid Integration

Verified on: 2026-05-20

Source:

- https://www.twilio.com/docs/sendgrid/ui/account-and-settings/api-keys

Prompteer uses `SENDGRID_API_KEY` for real email delivery. Empty values select the mock email client, which writes captured messages under `.mock/email/` and exposes them through dev-only API routes.
