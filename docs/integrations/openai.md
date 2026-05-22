# OpenAI Integration

Verified on: 2026-05-23

Sources:

- https://developers.openai.com/api/reference/overview
- https://developers.openai.com/api/reference/resources/chat/subresources/completions/methods/create
- https://developers.openai.com/api/reference/resources/chat/subresources/completions/streaming-events
- https://developers.openai.com/api/docs/models/gpt-4.1-mini

Prompteer uses `OPENAI_API_KEY` for real OpenAI access. When it is blank and `ANTHROPIC_API_KEY` is also blank, the API selects the deterministic mock LLM client.

`OPENAI_BASE_URL` defaults to `https://api.openai.com/v1` and exists for tests, proxies, or local upstream-shaped mocks. `OPENAI_CHAT_MODEL` defaults to `gpt-4.1-mini`, which the current OpenAI model reference lists as Chat Completions-compatible.

## Local mock

The dev mock exposes `POST /v1/chat/completions` and returns a deterministic Chat Completions response for the same request body:

```json
{
  "id": "chatcmpl_mock_<digest>",
  "object": "chat.completion",
  "created": 1750000000,
  "model": "gpt-4.1-mini",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "Mock Prompteer response <digest>: ...",
        "refusal": null
      },
      "finish_reason": "stop",
      "logprobs": null
    }
  ],
  "usage": {
    "prompt_tokens": 12,
    "completion_tokens": 8,
    "total_tokens": 20
  },
  "system_fingerprint": "fp_mock_<digest>"
}
```

When `stream: true`, the route emits Server-Sent Events using `chat.completion.chunk` payloads and terminates with `data: [DONE]`. If `stream_options.include_usage` is true, the final chunk includes `usage`.

The mock validates `model`, `messages[]`, and `n`, supports simple `stop`, `max_tokens`, and `max_completion_tokens` handling, and keeps IDs, timestamps, token counts, and text stable for identical inputs.
