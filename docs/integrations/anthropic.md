# Anthropic Integration

Verified on: 2026-05-20

Sources:

- https://docs.anthropic.com/en/api/overview
- https://docs.anthropic.com/en/api/messages
- https://docs.anthropic.com/en/docs/build-with-claude/streaming
- https://docs.anthropic.com/en/docs/about-claude/models/all-models

Prompteer uses `ANTHROPIC_API_KEY` for real Anthropic Messages access when OpenAI is not configured. When both LLM keys are blank, Prompteer uses deterministic local mock responses.

`ANTHROPIC_BASE_URL` defaults to `https://api.anthropic.com/v1`. `ANTHROPIC_MODEL` defaults to `claude-sonnet-4-20250514`, one of Anthropic's documented API model names. `ANTHROPIC_VERSION` defaults to `2023-06-01` and is sent as the `anthropic-version` header for real API calls.

## Local mock

The dev mock exposes `POST /v1/messages` and returns a deterministic Messages response for the same request body:

```json
{
  "id": "msg_mock_<digest>",
  "type": "message",
  "role": "assistant",
  "model": "claude-3-7-sonnet-latest",
  "content": [
    {
      "type": "text",
      "text": "Mock Prompteer response <digest>: ..."
    }
  ],
  "stop_reason": "end_turn",
  "stop_sequence": null,
  "usage": {
    "input_tokens": 12,
    "output_tokens": 8
  }
}
```

When `stream: true`, the route emits Anthropic-shaped SSE events: `message_start`, `content_block_start`, `content_block_delta`, `content_block_stop`, `message_delta`, and `message_stop`.

The mock validates `model`, `max_tokens`, and `messages[]`, supports simple `stop_sequences` and `max_tokens` handling, and keeps IDs, token counts, and text stable for identical inputs.
