from abc import ABC, abstractmethod

from app.schemas import ChatMessage


class ModelProvider(ABC):
    model_name: str

    @abstractmethod
    async def generate(self, prompt: str, *, system: str | None = None) -> str:
        """Generate text from a single prompt."""

    @abstractmethod
    async def chat(self, messages: list[ChatMessage], *, system: str | None = None) -> str:
        """Generate text from chat messages."""
