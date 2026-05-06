from app.config import Settings
from app.providers.base import ModelProvider
from app.providers.mock_provider import MockProvider
from app.providers.openai_provider import OpenAICompatibleProvider
from app.providers.vllm_provider import VLLMProvider


def build_provider(settings: Settings) -> ModelProvider:
    provider_name = settings.provider.lower()
    if provider_name == "openai":
        return OpenAICompatibleProvider(settings)
    if provider_name == "vllm":
        return VLLMProvider(settings)
    return MockProvider(settings)
