from app.config import Settings
from app.providers.openai_provider import OpenAICompatibleProvider


class VLLMProvider(OpenAICompatibleProvider):
    def __init__(self, settings: Settings):
        settings.openai_base_url = settings.vllm_base_url or settings.openai_base_url
        settings.openai_api_key = settings.vllm_api_key or settings.openai_api_key or "local-vllm"
        super().__init__(settings)
