# OpenAI Integration

Verified on: 2026-05-20

Source:

- https://platform.openai.com/docs/api-reference/introduction

Prompteer uses `OPENAI_API_KEY` for real OpenAI access. When it is blank and `ANTHROPIC_API_KEY` is also blank, the API selects the deterministic mock LLM client.

The mock Chat Completions response preserves the upstream shape used by legacy-compatible prompt runs: `id`, `object`, `created`, `model`, `choices[]`, `usage`, and `system_fingerprint`.
