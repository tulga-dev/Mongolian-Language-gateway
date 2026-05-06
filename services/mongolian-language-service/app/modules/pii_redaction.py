import re

PHONE_RE = re.compile(r"(?<!\d)(?:\+?976[-\s]?)?(?:\d[-\s]?){8}(?!\d)")
EMAIL_RE = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
REGISTER_RE = re.compile(r"\b[А-ЯӨҮЁ]{2}\d{8}\b", re.IGNORECASE)


def redact_pii(text: str) -> str:
    redacted = PHONE_RE.sub("[REDACTED_PHONE]", text)
    redacted = EMAIL_RE.sub("[REDACTED_EMAIL]", redacted)
    redacted = REGISTER_RE.sub("[REDACTED_REGISTER]", redacted)
    return redacted
