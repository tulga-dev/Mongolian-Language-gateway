import json
import re
from collections import Counter
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
DATASET_PATH = REPO_ROOT / "datasets" / "processed" / "lendex_500_sft.jsonl"
EXPECTED_DOMAINS = {
    "borrower_chat",
    "extraction",
    "compliance_rewrite",
    "finance_translation",
    "missing_field_clarification",
}
PHONE_RE = re.compile(r"(?<!\d)(?:\+?976[-\s]?)?(?:\d[-\s]?){8}(?!\d)")
EMAIL_RE = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
REGISTER_RE = re.compile(r"\b[\u0410-\u042f\u0401\u04e8\u04ae]{2}\d{8}\b", re.IGNORECASE)
UNSAFE_ASSISTANT_PHRASES = [
    "\u0437\u0430\u0430\u0432\u0430\u043b \u0431\u0430\u0442\u0430\u043b\u043d\u0430",
    "\u0431\u0430\u0442\u0430\u043b\u0433\u0430\u0430\u0442\u0430\u0439 \u0437\u04e9\u0432\u0448\u04e9\u04e9\u0440\u043d\u04e9",
    "guaranteed approval",
    "final approval is confirmed",
]


def load_dataset() -> list[dict]:
    with DATASET_PATH.open("r", encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def test_lendex_500_sft_has_expected_size_and_domains():
    records = load_dataset()
    counts = Counter(record["domain"] for record in records)
    assert len(records) == 500
    assert set(counts) == EXPECTED_DOMAINS
    assert all(count == 100 for count in counts.values())


def test_lendex_500_sft_messages_and_metadata_are_valid():
    records = load_dataset()
    for record in records:
        assert record["source"] == "synthetic_lendex_datagate_v1"
        assert record["license_status"] == "synthetic"
        assert record["allowed_usage"] == "training_allowed"
        assert record["contains_pii"] is False
        assert [message["role"] for message in record["messages"]] == ["system", "user", "assistant"]
        assert all(message["content"].strip() for message in record["messages"])


def test_lendex_500_sft_has_no_real_pii_patterns():
    joined = "\n".join(json.dumps(record, ensure_ascii=False) for record in load_dataset())
    assert PHONE_RE.search(joined) is None
    assert EMAIL_RE.search(joined) is None
    assert REGISTER_RE.search(joined) is None


def test_lendex_500_sft_assistant_is_polite_and_does_not_promise_approval():
    for record in load_dataset():
        assistant = record["messages"][-1]["content"]
        assistant_lower = assistant.lower()
        assert "\u0422\u0430" in assistant
        assert "\u044d\u0446\u0441\u0438\u0439\u043d" in assistant_lower
        for phrase in UNSAFE_ASSISTANT_PHRASES:
            assert phrase not in assistant_lower
