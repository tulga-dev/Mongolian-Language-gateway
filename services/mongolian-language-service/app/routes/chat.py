import re

from fastapi import APIRouter, Request

from app.modules.compliance import check_lending_compliance
from app.modules.confidence import heuristic_confidence
from app.modules.pii_redaction import redact_pii
from app.schemas import ChatRequest, ChatResponse, Language

router = APIRouter(prefix="/v1", tags=["chat"])

CYRILLIC_RE = re.compile(r"[\u0410-\u044f\u0401\u0451\u04e8\u04e9\u04ae\u04af]")
LATIN_RE = re.compile(r"[A-Za-z]")
REQUIRED_APPLICATION_FIELDS = [
    "loan_amount",
    "loan_term_months",
    "monthly_income",
    "employment_status",
    "collateral",
    "loan_type",
    "phone_number",
]


def detect_dominant_language(text: str) -> Language:
    cyrillic_count = len(CYRILLIC_RE.findall(text))
    latin_count = len(LATIN_RE.findall(text))
    if latin_count > cyrillic_count:
        return Language.english
    return Language.mongolian


def missing_fields(context: dict) -> list[str]:
    aliases = {
        "loan_term_months": ["loan_term_months", "term"],
        "monthly_income": ["monthly_income", "income"],
        "employment_status": ["employment_status", "employment"],
    }
    missing: list[str] = []
    for field in REQUIRED_APPLICATION_FIELDS:
        keys = aliases.get(field, [field])
        if not any(context.get(key) for key in keys):
            missing.append(field)
    return missing


@router.post("/chat", response_model=ChatResponse)
async def chat(payload: ChatRequest, request: Request) -> ChatResponse:
    provider = request.app.state.provider
    latest_user = next((m.content for m in reversed(payload.messages) if m.role == "user"), "")
    redacted_latest_user = redact_pii(latest_user)
    language = detect_dominant_language(redacted_latest_user)
    missing = missing_fields(payload.borrower_context)
    system = (
        "You are a polite borrower support assistant for Lendex and Datagate. "
        "Default to Mongolian. If the user writes Mongolian, answer in Mongolian; English, answer in English; "
        "mixed, answer in the dominant language. Use polite 'Ta' for Mongolian borrowers. "
        "Never promise loan approval. Ask for missing loan application fields when needed. "
        f"Missing fields: {', '.join(missing) if missing else 'none'}."
    )
    answer = await provider.chat(payload.messages, system=system)
    issues, _ = check_lending_compliance(answer) if payload.compliance_sensitive else ([], None)
    return ChatResponse(
        answer=answer,
        language=language,
        confidence=heuristic_confidence(answer, [issue.category for issue in issues]),
        missing_application_fields=missing,
        compliance_warnings=[issue.category for issue in issues],
        model=provider.model_name,
    )
