# SendGrid Integration

Verified on: 2026-05-20

Source:

- https://www.twilio.com/docs/sendgrid/ui/account-and-settings/api-keys
- https://www.twilio.com/docs/sendgrid/api-reference/mail-send/mail-send

Prompteer uses `SENDGRID_API_KEY` for real email delivery. Empty values select the mock email client, which writes captured messages under `.mock/email/` and exposes them through dev-only API routes.

## Current Mock Behavior

Implemented in `apps/api/app/integrations/email/mock.py`.

The mock validates the SendGrid Mail Send payload shape used by Prompteer:

- `personalizations[].to[].email`
- `from.email`
- `subject`
- `content[].type`
- `content[].value`
- optional `template_id`
- optional `dynamic_template_data`

Accepted messages are written as `.eml` files under `.mock/email/`. The mock also exposes the upstream-shaped Mail Send endpoint locally:

```http
POST /v3/mail/send
```

Successful mock sends return `202 Accepted` with an empty body, matching the SendGrid Mail Send success response shape.

Development mailbox route:

```http
GET /api/v1/dev/mailbox
GET /api/v1/dev/mailbox/{message_id}
```

These routes are available only when dev routes are enabled and the app is not running in production. `make seed` writes deterministic captured emails for the demo accounts so the mailbox has readable local data after first setup.
