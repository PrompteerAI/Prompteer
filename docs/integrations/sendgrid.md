# SendGrid Integration

Verified on: 2026-05-22

Source:

- https://www.twilio.com/docs/sendgrid/ui/account-and-settings/api-keys
- https://www.twilio.com/docs/sendgrid/api-reference/mail-send/mail-send
- https://www.twilio.com/docs/sendgrid/api-reference/mail-send/errors

Prompteer uses `SENDGRID_API_KEY` for real email delivery. Empty values select the mock email client, which writes captured messages under `.mock/email/` by default and exposes them through dev-only API routes. `MOCK_MAILBOX_DIR` can override the capture directory; Compose sets it to a writable in-container path.

## Current Mock Behavior

Implemented in `apps/api/app/integrations/email/mock.py`.

The mock validates the SendGrid Mail Send payload shape used by Prompteer:

- `personalizations[].to[].email`
- `from.email`
- `subject` at the message level, or `personalizations[].subject`, unless a template
  supplies the subject
- `content[].type`
- `content[].value`
- optional `template_id`
- optional `personalizations[].dynamic_template_data`

The mock follows SendGrid's transactional template exceptions: `content` is
required unless `template_id` is provided, and `subject` can be omitted when a
template supplies it. Captured template emails include the template id and dynamic
template data in the `.eml` body so local debugging remains useful.

Accepted messages are written as `.eml` files under the configured mock mailbox
directory. Native dev defaults to `.mock/email/`; Docker Compose sets
`MOCK_MAILBOX_DIR` to a writable in-container path and exposes those messages
through the dev mailbox routes. The mock also exposes the upstream-shaped Mail
Send endpoint locally:

```http
POST /v3/mail/send
```

Successful mock sends return `202 Accepted` with an empty body, matching the SendGrid Mail Send success response shape. Invalid payloads return Prompteer RFC 9457 Problem Details with `code: "sendgrid_payload_invalid"` and a SendGrid-style `errors[]` array containing `message`, `field`, and `help` entries.

Development mailbox route:

```http
GET /api/v1/dev/mailbox
GET /api/v1/dev/mailbox/{message_id}
```

These routes are available only when dev routes are enabled and the app is not running in production; disabled dev routes return normal Prompteer Problem Details instead of exposing mock-only endpoints. Development startup and `make seed` both write deterministic captured emails for the demo accounts so the mailbox has readable local data after first setup.
