import re

from fastapi import APIRouter, Request

from app.modules.confidence import heuristic_confidence
from app.modules.logging import safe_log_text
from app.modules.pii_redaction import PHONE_RE, redact_pii
from app.schemas import ExtractionRequest, ExtractionResponse, LoanApplicationExtraction

router = APIRouter(prefix="/v1", tags=["extraction"])

AMOUNT_RE = re.compile(r"(?P<amount>\d[\d,\.\s]*(?:сая|саяар|төгрөг|₮|mnt|million)?)", re.IGNORECASE)
TERM_RE = re.compile(r"(?P<term>\d+\s*(?:сар|сарын|жил|жилийн|month|months|year|years))", re.IGNORECASE)
INCOME_RE = re.compile(r"(?:орлого|income)[^\d]*(?P<income>\d[\d,\.\s]*(?:төгрөг|₮|mnt)?)", re.IGNORECASE)
EMPLOYMENT_TERMS = ["ажилтай", "хувиараа", "self-employed", "employed", "цалинтай"]
COLLATERAL_TERMS = ["байр", "машин", "орон сууц", "үл хөдлөх", "car", "apartment", "property"]
LOAN_TYPE_TERMS = ["хэрэглээний", "бизнес", "орон сууц", "business", "consumer", "mortgage"]


def first_match(pattern: re.Pattern[str], text: str, group: str) -> str | None:
    match = pattern.search(text)
    if not match:
        return None
    return match.group(group).strip()


def find_term(text: str, terms: list[str]) -> str | None:
    lowered = text.lower()
    return next((term for term in terms if term.lower() in lowered), None)


@router.post("/extract", response_model=ExtractionResponse)
async def extract(payload: ExtractionRequest, request: Request) -> ExtractionResponse:
    provider = request.app.state.provider
    redacted_text = redact_pii(payload.text) if payload.redact_pii else payload.text
    _ = safe_log_text(payload.text)

    extraction = LoanApplicationExtraction(
        loan_amount=first_match(AMOUNT_RE, payload.text, "amount"),
        term=first_match(TERM_RE, payload.text, "term"),
        income=first_match(INCOME_RE, payload.text, "income"),
        employment=find_term(payload.text, EMPLOYMENT_TERMS),
        collateral=find_term(payload.text, COLLATERAL_TERMS),
        loan_type=find_term(payload.text, LOAN_TYPE_TERMS),
        phone_number=PHONE_RE.search(payload.text).group(0) if PHONE_RE.search(payload.text) else None,
    )
    extraction.missing_fields = [
        field
        for field, value in extraction.model_dump(exclude={"missing_fields"}).items()
        if value is None
    ]

    return ExtractionResponse(
        extraction=extraction,
        redacted_text=redacted_text,
        confidence=heuristic_confidence(redacted_text, extraction.missing_fields),
        model=provider.model_name,
    )
