from fastapi import FastAPI

from app.config import get_settings
from app.modules.logging import configure_logging
from app.providers import build_provider
from app.routes import chat, compliance_check, evaluate, extract, rewrite, translate
from app.schemas import HealthResponse

settings = get_settings()
configure_logging(settings.log_level)
provider = build_provider(settings)

app = FastAPI(
    title="Mongolian Language Service",
    version="0.1.0",
    description="Mongolian-native Qwen service for Lendex and Datagate language workflows.",
)

app.state.settings = settings
app.state.provider = provider

app.include_router(translate.router)
app.include_router(chat.router)
app.include_router(extract.router)
app.include_router(rewrite.router)
app.include_router(compliance_check.router)
app.include_router(evaluate.router)


@app.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(
        status="ok",
        service=settings.service_name,
        provider=settings.provider,
        production_model=settings.production_model,
        teacher_model=settings.teacher_model,
    )
