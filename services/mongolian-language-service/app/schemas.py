from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field


class Language(str, Enum):
    mongolian = "mn"
    english = "en"
    auto = "auto"


class Domain(str, Enum):
    general = "general"
    finance = "finance"
    legal = "legal"
    lending = "lending"
    borrower_support = "borrower_support"


class Tone(str, Enum):
    neutral = "neutral"
    polite = "polite"
    borrower_friendly = "borrower_friendly"
    formal = "formal"
    legal = "legal"


class HealthResponse(BaseModel):
    status: Literal["ok"]
    service: str
    provider: str
    production_model: str
    teacher_model: str


class TranslationRequest(BaseModel):
    text: str = Field(..., min_length=1)
    source_language: Language = Language.auto
    target_language: Language
    domain: Domain = Domain.general
    tone: Tone = Tone.neutral
    glossary_id: str | None = None
    compliance_sensitive: bool = False
    require_human_review: bool = False


class TranslationResponse(BaseModel):
    translation: str
    confidence: float = Field(..., ge=0, le=1)
    requires_human_review: bool
    reason: str | None = None
    terms_used: list[str] = Field(default_factory=list)
    model: str
    glossary_warnings: list[str] = Field(default_factory=list)


class ChatMessage(BaseModel):
    role: Literal["system", "user", "assistant"]
    content: str


class ChatRequest(BaseModel):
    messages: list[ChatMessage] = Field(..., min_length=1)
    borrower_context: dict[str, Any] = Field(default_factory=dict)
    domain: Domain = Domain.borrower_support
    glossary_id: str | None = None
    compliance_sensitive: bool = True


class ChatResponse(BaseModel):
    answer: str
    language: Language
    confidence: float = Field(..., ge=0, le=1)
    missing_application_fields: list[str] = Field(default_factory=list)
    compliance_warnings: list[str] = Field(default_factory=list)
    model: str


class ExtractionRequest(BaseModel):
    text: str = Field(..., min_length=1)
    language: Language = Language.auto
    redact_pii: bool = True


class LoanApplicationExtraction(BaseModel):
    loan_amount: int | None = None
    loan_term_months: int | None = None
    monthly_income: int | None = None
    employment_status: str | None = None
    collateral: str | None = None
    loan_type: str | None = None
    phone_number: str | None = None
    missing_fields: list[str] = Field(default_factory=list)


class ExtractionResponse(BaseModel):
    extraction: LoanApplicationExtraction
    redacted_text: str
    confidence: float = Field(..., ge=0, le=1)
    model: str


class RewriteRequest(BaseModel):
    text: str = Field(..., min_length=1)
    target_language: Language = Language.mongolian
    tone: Tone = Tone.borrower_friendly
    compliance_sensitive: bool = True
    glossary_id: str | None = None


class RewriteResponse(BaseModel):
    rewritten_text: str
    compliance_warnings: list[str] = Field(default_factory=list)
    safer_alternatives: list[str] = Field(default_factory=list)
    confidence: float = Field(..., ge=0, le=1)
    model: str


class ComplianceCheckRequest(BaseModel):
    text: str = Field(..., min_length=1)
    language: Language = Language.auto
    domain: Domain = Domain.lending


class ComplianceIssue(BaseModel):
    category: str
    phrase: str
    severity: Literal["low", "medium", "high"]
    explanation: str
    safer_mongolian_alternative: str


class ComplianceCheckResponse(BaseModel):
    is_safe: bool
    issues: list[ComplianceIssue] = Field(default_factory=list)
    safer_text: str | None = None


class GlossaryCheckRequest(BaseModel):
    text: str = Field(..., min_length=1)
    glossary_id: str | None = None
    domain: Domain = Domain.finance


class GlossaryCheckResponse(BaseModel):
    terms_used: list[str] = Field(default_factory=list)
    glossary_warnings: list[str] = Field(default_factory=list)
    preferred_terms: dict[str, str] = Field(default_factory=dict)


class EvaluationItem(BaseModel):
    id: str
    input: str
    expected: str | None = None
    domain: Domain = Domain.general
    metadata: dict[str, Any] = Field(default_factory=dict)


class EvaluationRequest(BaseModel):
    benchmark_name: str
    items: list[EvaluationItem] = Field(..., min_length=1)
    judge_model: str | None = None


class EvaluationScore(BaseModel):
    item_id: str
    score: float = Field(..., ge=0, le=1)
    notes: str


class EvaluationResponse(BaseModel):
    benchmark_name: str
    average_score: float = Field(..., ge=0, le=1)
    scores: list[EvaluationScore]
    judge_model: str
