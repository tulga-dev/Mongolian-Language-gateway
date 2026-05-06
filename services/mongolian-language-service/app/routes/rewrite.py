from fastapi import APIRouter, Request

from app.modules.compliance import check_lending_compliance, safer_alternatives
from app.modules.confidence import heuristic_confidence
from app.modules.glossary import Glossary
from app.schemas import RewriteRequest, RewriteResponse

router = APIRouter(prefix="/v1", tags=["rewrite"])


@router.post("/rewrite", response_model=RewriteResponse)
async def rewrite(payload: RewriteRequest, request: Request) -> RewriteResponse:
    provider = request.app.state.provider
    glossary = Glossary(request.app.state.settings.glossary_dir)
    _, glossary_warnings, _ = glossary.check(payload.text, payload.glossary_id)
    issues, safer_text = check_lending_compliance(payload.text) if payload.compliance_sensitive else ([], None)
    system = (
        "Rewrite lending text in safe, polite Mongolian unless another target language is requested. "
        "Do not promise approval; include final review disclaimers where relevant."
    )
    prompt = (
        f"Target language: {payload.target_language.value}. Tone: {payload.tone.value}.\n"
        f"Text: {safer_text or payload.text}"
    )
    rewritten = await provider.generate(prompt, system=system)
    warnings = glossary_warnings + [issue.category for issue in issues]
    return RewriteResponse(
        rewritten_text=rewritten,
        compliance_warnings=[issue.category for issue in issues],
        safer_alternatives=safer_alternatives(issues),
        confidence=heuristic_confidence(rewritten, warnings),
        model=provider.model_name,
    )
