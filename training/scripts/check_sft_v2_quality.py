from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path

MONGOLIAN_RE = re.compile(r"[\u0410-\u044f\u0401\u0451\u04e8\u04e9\u04ae\u04af]")
ENGLISH_RE = re.compile(r"[A-Za-z]")
METRIC_TERMS = [
    "ашиг",
    "ашгийн маржин",
    "өр/орлого",
    "мөнгө/өр",
    "зардлын харьцаа",
    "сарын ойролцоо төлөлт",
    "барьцааны бүрхэлт",
    "төлөлтийн дараах",
]
FORBIDDEN = [
    "<think>",
    "</think>",
    "chain-of-thought",
    "reasoning:",
    "[Огноог нэмнэ]",
    "[огноог нэмнэ]",
]
REQUIRED_DOMAINS = {
    "credit_memo",
    "borrower_risk_classification",
    "financial_ratio_explanation",
    "loan_application_summary",
    "collateral_assessment",
    "repayment_capacity_analysis",
    "red_flag_detection",
    "lender_recommendation",
    "financial_statement_summary",
    "cash_flow_lending_decision",
}


def fail(path: Path, line_number: int, message: str) -> None:
    raise SystemExit(f"{path}:{line_number}: {message}")


def load(path: Path) -> list[tuple[int, dict]]:
    rows = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            rows.append((line_number, json.loads(line)))
    return rows


def assistant_text(row: dict) -> str:
    messages = row.get("messages")
    if not isinstance(messages, list) or len(messages) < 3:
        return ""
    return messages[-1].get("content", "")


def metadata(row: dict) -> dict:
    return row.get("metadata", {})


def mongolian_char_count(text: str) -> int:
    return len(MONGOLIAN_RE.findall(text))


def mostly_english(text: str) -> bool:
    english = len(ENGLISH_RE.findall(text))
    mongolian = mongolian_char_count(text)
    return english > mongolian * 0.35


def metric_count(text: str) -> int:
    lowered = text.lower()
    return sum(1 for term in METRIC_TERMS if term in lowered)


def validate_row(path: Path, line_number: int, row: dict) -> tuple[str, str]:
    meta = metadata(row)
    domain = meta.get("domain")
    source = meta.get("source")
    messages = row.get("messages")
    if domain not in REQUIRED_DOMAINS:
        fail(path, line_number, f"missing or invalid domain: {domain}")
    if meta.get("contains_pii") is not False:
        fail(path, line_number, "contains_pii must be false")
    if source != "synthetic_lendex_credit_analyst_v2":
        fail(path, line_number, "unexpected source metadata")
    if not isinstance(messages, list) or [m.get("role") for m in messages] != ["system", "user", "assistant"]:
        fail(path, line_number, "messages must use system/user/assistant format")

    output = assistant_text(row)
    lowered = output.lower()
    for forbidden in FORBIDDEN:
        if forbidden.lower() in lowered:
            fail(path, line_number, f"forbidden text found: {forbidden}")
    if mostly_english(output):
        fail(path, line_number, "assistant output is mostly English")
    if mongolian_char_count(output) < 80:
        fail(path, line_number, "assistant output is shorter than 80 Mongolian characters")
    if "эрсдэл" not in lowered and domain != "financial_ratio_explanation":
        fail(path, line_number, "risk level or risk discussion is missing")
    if domain == "credit_memo":
        required = ["Эрсдэлийн түвшин", "Шийдвэрийн үндэслэл", "Дутуу баримт", "Санал"]
        for item in required:
            if item not in output:
                fail(path, line_number, f"credit memo missing required field: {item}")
    if meta.get("numeric_example") is True and metric_count(output) < 1:
        fail(path, line_number, "numeric example has no calculated metric")
    return domain, source


def main() -> None:
    parser = argparse.ArgumentParser(description="Check Lendex SFT v2 dataset quality.")
    parser.add_argument("path", type=Path)
    args = parser.parse_args()

    rows = load(args.path)
    if not rows:
        raise SystemExit(f"{args.path}: no rows found")
    domain_counts: Counter[str] = Counter()
    source_counts: Counter[str] = Counter()
    for line_number, row in rows:
        domain, source = validate_row(args.path, line_number, row)
        domain_counts[domain] += 1
        source_counts[source] += 1
    missing_domains = REQUIRED_DOMAINS - set(domain_counts)
    if missing_domains:
        raise SystemExit(f"{args.path}: missing domains: {sorted(missing_domains)}")
    print(
        json.dumps(
            {
                "path": str(args.path),
                "rows": len(rows),
                "domains": domain_counts,
                "sources": source_counts,
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
