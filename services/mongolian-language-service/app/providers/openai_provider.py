import httpx

from app.config import Settings
from app.providers.base import ModelProvider
from app.schemas import ChatMessage


class OpenAICompatibleProvider(ModelProvider):
    def __init__(self, settings: Settings):
        if not settings.openai_base_url or not settings.openai_api_key:
            raise ValueError("OPENAI_BASE_URL and OPENAI_API_KEY are required for MODEL_PROVIDER=openai")
        self.base_url = settings.openai_base_url.rstrip("/")
        self.api_key = settings.openai_api_key
        self.model_name = settings.production_model

    async def generate(self, prompt: str, *, system: str | None = None) -> str:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        return await self._chat_completion(messages)

    async def chat(self, messages: list[ChatMessage], *, system: str | None = None) -> str:
        payload_messages = []
        if system:
            payload_messages.append({"role": "system", "content": system})
        payload_messages.extend(m.model_dump() for m in messages)
        return await self._chat_completion(payload_messages)

    async def _chat_completion(self, messages: list[dict[str, str]]) -> str:
        headers = {"Authorization": f"Bearer {self.api_key}"}
        payload = {"model": self.model_name, "messages": messages, "temperature": 0.2}
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
            )
            response.raise_for_status()
            data = response.json()
        return data["choices"][0]["message"]["content"]
