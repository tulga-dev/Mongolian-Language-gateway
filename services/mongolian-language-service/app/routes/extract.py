import re

from fastapi import APIRouter, Request

from app.modules.confidence import heuristic_confidence
from app.modules.logging import safe_log_text
from app.modules.pii_redaction import PHONE_RE, redact_pii
from app.schemas import ExtractionRequest, ExtractionResponse, LoanApplicationExtraction

router = APIRouter(prefix="/v1", tags=["extraction"])

NUMBER_WORD_MULTIPLIERS = {
    "\u0441\u0430\u044f": 1_000_000,
    "\u0441\u0430\u044f\u0430\u0440": 1_000_000,
    "million": 1_000_000,
}
MONEY_RE = re.compile(
    r"(?P<number>\d[\d,.\s]*)(?:\s*(?P<unit>\u0441\u0430\u044f\u0430\u0440|\u0441\u0430\u044f|million))?"
    r"(?:\s*(?:\u0442\u04e9\u0433\u0440\u04e9\u0433|\u0442\u04e9\u0433|mnt|m\u043d\u0442|\u20ae))?",
    re.IGNORECASE,
)
TERM_RE = re.compile(
    r"(?P<number>\d+)\s*(?P<unit>\u0441\u0430\u0440\u0430\u0430\u0440|\u0441\u0430\u0440\u044b\u043d|\u0441\u0430\u0440|\u0436\u0438\u043b\u0438\u0439\u043d|\u0436\u0438\u043b|months?|years?)",
    re.IGNORECASE,
)
INCOME_CONTEXT_RE = re.compile(
    r"(?:\u043e\u0440\u043b\u043e\u0433\u043e|\u0446\u0430\u043b\u0438\u043d|income|salary)[^\d]{0,24}"
    r"(?P<number>\d[\d,.\s]*)(?:\s*(?P<unit>\u0441\u0430\u044f\u0430\u0440|\u0441\u0430\u044f|million))?",
    re.IGNORECASE,
)
LOAN_CONTEXT_RE = re.compile(
    r"(?P<number>\d[\d,.\s]*)(?:\s*(?P<unit>\u0441\u0430\u044f\u0430\u0440|\u0441\u0430\u044f|million))?"
    r"(?:\s*(?:\u0442\u04e9\u0433\u0440\u04e9\u0433|\u0442\u04e9\u0433|mnt|m\u043d\u0442|\u20ae))?"
    r".{0,30}(?:\u0437\u044d\u044d\u043b|loan)",
    re.IGNORECASE,
)
EMPLOYMENT_TERMS = {
    "\u0430\u0436\u0438\u043b\u0442\u0430\u0439": "employed",
    "\u0446\u0430\u043b\u0438\u043d\u0442\u0430\u0439": "salaried",
    "\u0445\u0443\u0432\u0438\u0430\u0440\u0430\u0430": "self-employed",
    "self-employed": "self-employed",
    "employed": "employed",
    "salaried": "salaried",
}
COLLATERAL_TERMS = {
    "\u043c\u0430\u0448\u0438\u043d": "car",
    "\u0430\u0432\u0442\u043e\u043c\u0430\u0448\u0438\u043d": "car",
    "\u0431\u0430\u0439\u0440": "apartment",
    "\u043e\u0440\u043e\u043d \u0441\u0443\u0443\u0446": "apartment",
    "\u04af\u043b \u0445\u04e9\u0434\u043b\u04e9\u0445": "property",
    "car": "car",
    "apartment": "apartment",
    "property": "property",
}
LOAN_TYPE_TERMS = {
    "\u0445\u044d\u0440\u044d\u0433\u043b\u044d\u044d\u043d\u0438\u0439": "consumer",
    "\u0431\u0438\u0437\u043d\u0435\u0441": "business",
    "\u043e\u0440\u043e\u043d \u0441\u0443\u0443\u0446": "mortgage",
    "business": "business",
    "consumer": "consumer",
    "mortgage": "mortgage",
}


def parse_number(value: str, unit: str | None = None) -> int | None:
    cleaned = re.sub(r"[^\d.]", "", value)
    if not cleaned:
        return None
    number = float(cleaned)
    multiplier = NUMBER_WORD_MULTIPLIERS.get((unit or "").lower(), 1)
    return int(number * multiplier)


def parse_term_months(text: str) -> int | None:
    match = TERM_RE.search(text)
    if not match:
        return None
    amount = int(match.group("number"))
    unit = match.group("unit").lower()
    if unit in {"year", "years", "\u0436\u0438\u043b", "\u0436\u0438\u043b\u0438\u0439\u043d"}:
        return amount * 12
    return amount


def parse_monthly_income(text: str) -> int | None:
    match = INCOME_CONTEXT_RE.search(text)
    if not match:
        return None
    return parse_number(match.group("number"), match.group("unit"))


def parse_loan_amount(text: str) -> int | None:
    match = LOAN_CONTEXT_RE.search(text)
    if match:
        return parse_number(match.group("number"), match.group("unit"))
    amounts = [parse_number(match.group("number"), match.group("unit")) for match in MONEY_RE.finditer(text)]
    amounts = [amount for amount in amounts if amount and amount >= 100_000]
    return amounts[0] if amounts else None


def find_term(text: str, terms: dict[str, str]) -> str | None:
    lowered = text.lower()
    return next((normalized for term, normalized in terms.items() if term.lower() in lowered), None)


def extract_phone(text: str) -> str | None:
    match = PHONE_RE.search(text)
    if not match:
        return None
    return re.sub(r"\D", "", match.group(0))[-8:]


@router.post("/extract", response_model=ExtractionResponse)
async def extract(payload: ExtractionRequest, request: Request) -> ExtractionResponse:
    provider = request.app.state.provider
    redacted_text = redact_pii(payload.text)
    _ = safe_log_text(payload.text)

    extraction = LoanApplicationExtraction(
        loan_amount=parse_loan_amount(payload.text),
        loan_term_months=parse_term_months(payload.text),
        monthly_income=parse_monthly_income(payload.text),
        employment_status=find_term(payload.text, EMPLOYMENT_TERMS),
        collateral=find_term(payload.text, COLLATERAL_TERMS),
        loan_type=find_term(payload.text, LOAN_TYPE_TERMS),
        phone_number=extract_phone(payload.text),
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
