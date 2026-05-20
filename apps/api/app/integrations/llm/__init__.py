from app.core.config import settings
from app.integrations.llm.mock import MockLLMClient


def get_llm_client() -> MockLLMClient:
    # Real OpenAI and Anthropic clients will replace this once their typed adapters land.
    return MockLLMClient(
        provider="openai"
        if settings.openai_api_key
        else "anthropic"
        if settings.anthropic_api_key
        else "mock",
    )
