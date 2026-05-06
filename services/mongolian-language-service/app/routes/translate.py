from fastapi import APIRouter, Request

from app.modules.compliance import check_lending_compliance
from app.modules.confidence import heuristic_confidence
from app.modules.glossary import Glossary
from app.schemas import GlossaryCheckRequest, GlossaryCheckResponse, TranslationRequest, TranslationResponse

router = APIRouter(prefix="/v1", tags=["translation"])


@router.post("/translate", response_model=TranslationResponse)
async def translate(payload: TranslationRequest, request: Request) -> TranslationResponse:
    provider = request.app.state.provider
    glossary = Glossary(request.app.state.settings.glossary_dir)
    terms_used, glossary_warnings, _ = glossary.check(payload.text, payload.glossary_id)
    issues, _ = check_lending_compliance(payload.text) if payload.compliance_sensitive else ([], None)

    system = (
        "You are a Mongolian-native Qwen translation model. Preserve meaning, use preferred "
        "financial/legal terminology, and avoid promising loan approval."
    )
    prompt = (
        f"Translate from {payload.source_language.value} to {payload.target_language.value}. "
        f"Domain: {payload.domain.value}. Tone: {payload.tone.value}.\n\n{payload.text}"
    )
    generated = await provider.generate(prompt, system=system)
    confidence = heuristic_confidence(generated, glossary_warnings + [issue.category for issue in issues])
    requires_review = payload.require_human_review or bool(issues) or confidence < 0.75
    reason = None
    if requires_review:
        reason = "Human review recommended due to compliance sensitivity, glossary warnings, or low confidence."

    return TranslationResponse(
        translation=generated,
        confidence=confidence,
        requires_human_review=requires_review,
        reason=reason,
        terms_used=terms_used,
        model=provider.model_name,
        glossary_warnings=glossary_warnings,
    )


@router.post("/glossary/check", response_model=GlossaryCheckResponse)
async def glossary_check(payload: GlossaryCheckRequest, request: Request) -> GlossaryCheckResponse:
    glossary = Glossary(request.app.state.settings.glossary_dir)
    terms_used, warnings, preferred_terms = glossary.check(payload.text, payload.glossary_id)
    return GlossaryCheckResponse(
        terms_used=terms_used,
        glossary_warnings=warnings,
        preferred_terms=preferred_terms,
    )
