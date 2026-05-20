"""LLM client factory selecting OpenAI, Anthropic, or deterministic mock mode."""

from app.core.config import settings
from app.integrations.llm.base import LLMClient
from app.integrations.llm.mock import MockLLMClient
from app.integrations.llm.real import AnthropicClient, OpenAIClient


def get_llm_client() -> LLMClient:
    if settings.openai_api_key:
        return OpenAIClient(api_key=settings.openai_api_key, base_url=settings.openai_base_url)
    if settings.anthropic_api_key:
        return AnthropicClient(
            api_key=settings.anthropic_api_key,
            base_url=settings.anthropic_base_url,
            anthropic_version=settings.anthropic_version,
        )
    return MockLLMClient()
