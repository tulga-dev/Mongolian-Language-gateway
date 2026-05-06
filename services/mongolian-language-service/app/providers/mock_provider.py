from app.config import Settings
from app.providers.base import ModelProvider
from app.schemas import ChatMessage


class MockProvider(ModelProvider):
    def __init__(self, settings: Settings):
        self.model_name = settings.production_model

    async def generate(self, prompt: str, *, system: str | None = None) -> str:
        del system
        return f"[mock-qwen] {prompt[:800]}"

    async def chat(self, messages: list[ChatMessage], *, system: str | None = None) -> str:
        del system
        latest_user = next((m.content for m in reversed(messages) if m.role == "user"), "")
        return f"[mock-qwen] {latest_user[:800]}"
