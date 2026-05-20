"""Deterministic LLM mock.

Schema references verified on 2026-05-20:
- OpenAI Chat Completions: https://platform.openai.com/docs/api-reference/chat/create
- Anthropic Messages: https://docs.anthropic.com/en/api/messages
"""

from dataclasses import dataclass
from hashlib import sha256
from time import time
from typing import Any


@dataclass(frozen=True)
class MockLLMClient:
    provider: str = "mock"

    async def chat_completion(self, payload: dict[str, Any]) -> dict[str, Any]:
        digest = sha256(repr(sorted(payload.items())).encode()).hexdigest()[:16]
        text = f"Mock Prompteer response {digest}"
        return {
            "id": f"chatcmpl_mock_{digest}",
            "object": "chat.completion",
            "created": int(time()),
            "model": str(payload.get("model", "mock-gpt")),
            "choices": [
                {
                    "index": 0,
                    "message": {"role": "assistant", "content": text},
                    "finish_reason": "stop",
                    "logprobs": None,
                }
            ],
            "usage": {"prompt_tokens": 12, "completion_tokens": 8, "total_tokens": 20},
            "system_fingerprint": f"fp_mock_{digest[:8]}",
        }

    async def anthropic_message(self, payload: dict[str, Any]) -> dict[str, Any]:
        digest = sha256(repr(sorted(payload.items())).encode()).hexdigest()[:16]
        return {
            "id": f"msg_mock_{digest}",
            "type": "message",
            "role": "assistant",
            "model": str(payload.get("model", "mock-claude")),
            "content": [{"type": "text", "text": f"Mock Prompteer response {digest}"}],
            "stop_reason": "end_turn",
            "stop_sequence": None,
            "usage": {"input_tokens": 12, "output_tokens": 8},
        }
