import logging

from app.modules.pii_redaction import redact_pii


class PiiRedactionFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.msg = redact_pii(str(record.getMessage()))
        record.args = ()
        return True


def configure_logging(level: str) -> None:
    logging.basicConfig(
        level=level.upper(),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    redaction_filter = PiiRedactionFilter()
    root_logger = logging.getLogger()
    root_logger.addFilter(redaction_filter)
    for handler in root_logger.handlers:
        handler.addFilter(redaction_filter)


def safe_log_text(text: str) -> str:
    return redact_pii(text)
