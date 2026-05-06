from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path

MONGOLIAN_RE = re.compile(r"[\u0410-\u044f\u0401\u0451\u04e8\u04e9\u04ae\u04af]")
ENGLISH_RE = re.compile(r"[A-Za-z]")
THINK_RE = re.compile(r"</?think\b", re.IGNORECASE)
BAD_PHRASES = [
    "Хуцлах хугацаа",
    "Өрийн дарамтын маргааш",
    "ашгийн хураамж",
    "дарамтын харьцаа",
    "дотоодын орлого",
    "төлбөр дуусгах чадвар",
    "зээл өгөнцөөр",
    "зардалын",
]
REQUIRED_NUMERIC_FIELDS = [
    "Тооцоолсон ашиг",
    "Ашгийн маржин",
    "Зардлын харьцаа",
    "Өр/орлогын харьцаа",
    "Мөнгө/өрийн харьцаа",
    "Эрсдэлийн түвшин",
    "Зөвлөмж",
]
STRICT_MEMO_DOMAINS = {"credit_memo_numeric", "lender_recommendation_numeric"}
NUMERIC_DOMAINS = {
    "credit_memo_numeric",
    "repayment_capacity_numeric",
    "lender_recommendation_numeric",
    "financial_ratios_numeric",
    "risk_classification_structured",
}
EXPECTED_DOMAIN_COUNTS = {
    "credit_memo_numeric": 500,
    "repayment_capacity_numeric": 300,
    "lender_recommendation_numeric": 250,
    "financial_ratios_numeric": 200,
    "risk_classification_structured": 150,
    "missing_documents_request": 100,
}


def fail(path: Path, line_number: int, message: str) -> None:
    raise SystemExit(f"FAIL {path}:{line_number}: {message}")


def load_rows(path: Path) -> list[tuple[int, dict]]:
    rows: list[tuple[int, dict]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if line.strip():
                rows.append((line_number, json.loads(line)))
    return rows


def assistant(row: dict) -> str:
    return row["messages"][-1]["content"]


def user_prompt(row: dict) -> str:
    return row["messages"][1]["content"]


def mostly_english(text: str) -> bool:
    english = len(ENGLISH_RE.findall(text))
    mongolian = len(MONGOLIAN_RE.findall(text))
    return english > mongolian * 0.25


def money(value: float) -> str:
    if abs(value - round(value)) < 0.01:
        return f"₮{int(round(value))} сая"
    return f"₮{value:.1f} сая"


def percent(value: float | None) -> str:
    if value is None:
        return "тооцох боломжгүй"
    return f"{value * 100:.1f}%"


def safe_div(numerator: float, denominator: float) -> float | None:
    if denominator == 0:
        return None
    return numerator / denominator


def parse_prompt_numbers(prompt: str) -> dict[str, int]:
    patterns = {
        "revenue": r"Орлого\s+(\d+)\s+сая",
        "expense": r"зардал\s+(\d+)\s+сая",
        "debt": r"өр төлбөр\s+(\d+)\s+сая",
        "cash": r"мөнгөн үлдэгдэл\s+(\d+)\s+сая",
        "loan_amount": r"хүссэн зээл\s+(\d+)\s+сая",
        "term_months": r"хугацаа\s+(\d+)\s+сар",
    }
    values: dict[str, int] = {}
    for key, pattern in patterns.items():
        match = re.search(pattern, prompt, re.IGNORECASE)
        if not match:
            raise ValueError(f"missing numeric field in prompt: {key}")
        values[key] = int(match.group(1))
    return values


def expected_metrics(values: dict[str, int]) -> dict[str, str]:
    profit = values["revenue"] - values["expense"]
    return {
        "Орлого": money(values["revenue"]),
        "Зардал": money(values["expense"]),
        "Тооцоолсон ашиг": money(profit),
        "Ашгийн маржин": percent(safe_div(profit, values["revenue"])),
        "Зардлын харьцаа": percent(safe_div(values["expense"], values["revenue"])),
        "Өр/орлогын харьцаа": percent(safe_div(values["debt"], values["revenue"])),
        "Мөнгө/өрийн харьцаа": percent(safe_div(values["cash"], values["debt"])),
        "Сарын төлбөрийн ойролцоо тооцоо": money(safe_div(values["loan_amount"], values["term_months"]) or 0),
    }


def metric_matches(output: str, metrics: dict[str, str]) -> int:
    lowered = output.lower()
    return sum(1 for label, value in metrics.items() if label.lower() in lowered and value in output)


def validate_row(path: Path, line_number: int, row: dict) -> tuple[str, str]:
    meta = row.get("metadata", {})
    domain = meta.get("domain")
    source = meta.get("source")
    output = assistant(row)
    lowered = output.lower()

    if domain not in EXPECTED_DOMAIN_COUNTS:
        fail(path, line_number, f"unknown domain {domain!r}")
    if source != "synthetic_lendex_credit_analyst_v3":
        fail(path, line_number, "unexpected source")
    if meta.get("contains_pii") is not False:
        fail(path, line_number, "contains_pii must be false")
    if THINK_RE.search(output):
        fail(path, line_number, "thinking tag found")
    for phrase in BAD_PHRASES:
        if phrase.lower() in lowered:
            fail(path, line_number, f"banned phrase found: {phrase}")
    if mostly_english(output):
        fail(path, line_number, "output is mostly English")
    if domain == "credit_memo_numeric" and len(MONGOLIAN_RE.findall(output)) < 250:
        fail(path, line_number, "credit memo output shorter than 250 Mongolian characters")
    if domain in STRICT_MEMO_DOMAINS:
        for field in REQUIRED_NUMERIC_FIELDS:
            if field not in output:
                fail(path, line_number, f"missing required numeric field: {field}")
    if domain in NUMERIC_DOMAINS:
        try:
            values = parse_prompt_numbers(user_prompt(row))
        except ValueError as exc:
            fail(path, line_number, str(exc))
        metrics = expected_metrics(values)
        required_labels = [
            "Тооцоолсон ашиг",
            "Ашгийн маржин",
            "Зардлын харьцаа",
            "Өр/орлогын харьцаа",
            "Мөнгө/өрийн харьцаа",
        ]
        if domain in STRICT_MEMO_DOMAINS:
            for label in required_labels:
                if metrics[label] not in output:
                    fail(path, line_number, f"metric mismatch for {label}: expected {metrics[label]}")
        if metric_matches(output, metrics) < 3:
            fail(path, line_number, "numeric output has fewer than 3 calculated metric matches")
    return domain, source


def expected_counts_for_size(total: int) -> dict[str, int] | None:
    if total == 1500:
        return EXPECTED_DOMAIN_COUNTS
    if total == 1350:
        return {domain: int(count * 0.9) for domain, count in EXPECTED_DOMAIN_COUNTS.items()}
    if total == 150:
        return {domain: count - int(count * 0.9) for domain, count in EXPECTED_DOMAIN_COUNTS.items()}
    return None


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate strict Lendex/DataGate SFT v3 JSONL quality.")
    parser.add_argument("path", type=Path)
    args = parser.parse_args()

    rows = load_rows(args.path)
    if not rows:
        raise SystemExit(f"FAIL {args.path}: empty dataset")
    domain_counts: Counter[str] = Counter()
    source_counts: Counter[str] = Counter()
    for line_number, row in rows:
        domain, source = validate_row(args.path, line_number, row)
        domain_counts[domain] += 1
        source_counts[source] += 1
    expected_counts = expected_counts_for_size(len(rows))
    if expected_counts and dict(domain_counts) != expected_counts:
        raise SystemExit(f"FAIL {args.path}: domain counts mismatch. got={dict(domain_counts)} expected={expected_counts}")
    print(json.dumps({
        "status": "PASS",
        "path": str(args.path),
        "rows": len(rows),
        "domains": domain_counts,
        "sources": source_counts,
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
