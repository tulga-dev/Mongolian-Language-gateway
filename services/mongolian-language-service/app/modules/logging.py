import logging

from app.modules.pii_redaction import redact_pii


def configure_logging(level: str) -> None:
    logging.basicConfig(
        level=level.upper(),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )


def safe_log_text(text: str) -> str:
    return redact_pii(text)
