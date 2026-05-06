import re

from app.config import Settings
from app.providers.base import ModelProvider
from app.schemas import ChatMessage

CYRILLIC_RE = re.compile(r"[\u0410-\u044f\u0401\u0451\u04e8\u04e9\u04ae\u04af]")


class MockProvider(ModelProvider):
    def __init__(self, settings: Settings):
        self.model_name = settings.production_model

    async def generate(self, prompt: str, *, system: str | None = None) -> str:
        del system
        if "Rewrite lending text" in prompt:
            return "[mock-qwen] Safe borrower-facing rewrite with final review disclaimer."
        if "Translate from" in prompt:
            return "[mock-qwen] Translation draft for human or automated review."
        return f"[mock-qwen] {prompt[:800]}"

    async def chat(self, messages: list[ChatMessage], *, system: str | None = None) -> str:
        latest_user = next((m.content for m in reversed(messages) if m.role == "user"), "")
        cyrillic_count = len(CYRILLIC_RE.findall(latest_user))
        latin_count = len(re.findall(r"[A-Za-z]", latest_user))
        missing_note = ""
        if system and "Missing fields: none" not in system:
            missing_note = " Please provide the missing application fields listed by the service."
        if latin_count > cyrillic_count:
            return (
                "[mock-qwen] I can help review your loan request, but approval is only decided "
                f"after final lender review.{missing_note}"
            )
        return (
            "[mock-qwen] \u0422\u0430\u043d\u044b \u0437\u044d\u044d\u043b\u0438\u0439\u043d "
            "\u0445\u04af\u0441\u044d\u043b\u0442\u0438\u0439\u0433 \u0445\u044f\u043d\u0430\u0436 "
            "\u04af\u0437\u044d\u0445 \u0431\u043e\u043b\u043e\u043c\u0436\u0442\u043e\u0439, "
            "\u0433\u044d\u0445\u0434\u044d\u044d \u044d\u0446\u0441\u0438\u0439\u043d "
            "\u0448\u0438\u0439\u0434\u0432\u044d\u0440 \u0437\u04e9\u0432\u0445\u04e9\u043d "
            "\u0445\u044f\u043d\u0430\u043b\u0442\u044b\u043d \u0434\u0430\u0440\u0430\u0430 "
            f"\u0433\u0430\u0440\u043d\u0430.{missing_note}"
        )
