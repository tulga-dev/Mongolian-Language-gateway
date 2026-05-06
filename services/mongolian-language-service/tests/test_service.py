from fastapi.testclient import TestClient

from app.main import app
from app.modules.logging import safe_log_text


client = TestClient(app)

MN_APPROVAL_ASK = "\u041c\u0438\u043d\u0438\u0439 \u0437\u044d\u044d\u043b \u0431\u0430\u0442\u043b\u0430\u0433\u0434\u0430\u0445 \u0443\u0443?"
MN_LOAN_FULL = (
    "\u0411\u0438 10 \u0441\u0430\u044f \u0442\u04e9\u0433\u0440\u04e9\u0433\u0438\u0439\u043d "
    "\u0445\u044d\u0440\u044d\u0433\u043b\u044d\u044d\u043d\u0438\u0439 \u0437\u044d\u044d\u043b "
    "24 \u0441\u0430\u0440\u044b\u043d \u0445\u0443\u0433\u0430\u0446\u0430\u0430\u0442\u0430\u0439 "
    "\u0430\u0432\u043c\u0430\u0430\u0440 \u0431\u0430\u0439\u043d\u0430. "
    "\u0421\u0430\u0440\u044b\u043d \u043e\u0440\u043b\u043e\u0433\u043e 2 \u0441\u0430\u044f, "
    "\u0446\u0430\u043b\u0438\u043d\u0442\u0430\u0439, \u0431\u0430\u0440\u044c\u0446\u0430\u0430\u043d\u0434 "
    "\u043c\u0430\u0448\u0438\u043d\u0442\u0430\u0439. \u0423\u0442\u0430\u0441 99112233."
)
MN_NO_INCOME = (
    "\u0411\u0438 5 \u0441\u0430\u044f \u0442\u04e9\u0433\u0440\u04e9\u0433\u0438\u0439\u043d "
    "\u0437\u044d\u044d\u043b 12 \u0441\u0430\u0440\u0430\u0430\u0440 \u0430\u0432\u043c\u0430\u0430\u0440 "
    "\u0431\u0430\u0439\u043d\u0430. 99112233"
)
MN_NO_TERM = (
    "\u0411\u0438 8 \u0441\u0430\u044f \u0442\u04e9\u0433\u0440\u04e9\u0433\u0438\u0439\u043d "
    "\u0437\u044d\u044d\u043b \u0430\u0432\u043c\u0430\u0430\u0440 \u0431\u0430\u0439\u043d\u0430. "
    "\u041e\u0440\u043b\u043e\u0433\u043e 3 \u0441\u0430\u044f. 99112233"
)
MN_UNSAFE_APPROVAL = "\u0422\u0430\u043d\u044b \u0437\u044d\u044d\u043b \u0437\u0430\u0430\u0432\u0430\u043b \u0431\u0430\u0442\u0430\u043b\u043d\u0430."
MN_MISLEADING_FEES = "\u0425\u04af\u04af \u0448\u0438\u043c\u0442\u0433\u044d\u043b\u0433\u04af\u0439 \u0445\u0430\u043c\u0433\u0438\u0439\u043d \u0431\u0430\u0433\u0430 \u0445\u04af\u04af\u0442\u044d\u0439."


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["production_model"] == "Qwen3-32B-MN-Lendex"
    assert body["teacher_model"] == "Qwen3-235B-A22B-Instruct-2507"


def test_translate_endpoint_flags_compliance_sensitive_text():
    response = client.post(
        "/v1/translate",
        json={
            "text": MN_UNSAFE_APPROVAL,
            "source_language": "mn",
            "target_language": "en",
            "domain": "lending",
            "tone": "formal",
            "glossary_id": "lendex_finance",
            "compliance_sensitive": True,
            "require_human_review": False,
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["model"] == "Qwen3-32B-MN-Lendex"
    assert body["requires_human_review"] is True
    assert 0 <= body["confidence"] <= 1


def test_chat_borrower_approval_request_is_safe_and_mongolian():
    response = client.post(
        "/v1/chat",
        json={
            "messages": [{"role": "user", "content": MN_APPROVAL_ASK}],
            "borrower_context": {"loan_amount": 5_000_000},
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["language"] == "mn"
    assert "loan_term_months" in body["missing_application_fields"]
    assert "monthly_income" in body["missing_application_fields"]
    assert body["compliance_warnings"] == []
    assert "\u0422\u0430" in body["answer"]


def test_chat_mixed_message_uses_dominant_language():
    response = client.post(
        "/v1/chat",
        json={
            "messages": [
                {
                    "role": "user",
                    "content": "Hello, I need loan approval please. \u0417\u044d\u044d\u043b?",
                }
            ],
            "borrower_context": {},
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["language"] == "en"
    assert "approval is only decided after final lender review" in body["answer"]


def test_extract_returns_normalized_lending_fields_and_redacts_phone():
    response = client.post("/v1/extract", json={"text": MN_LOAN_FULL})
    assert response.status_code == 200
    body = response.json()
    extraction = body["extraction"]
    assert extraction["loan_amount"] == 10_000_000
    assert extraction["loan_term_months"] == 24
    assert extraction["monthly_income"] == 2_000_000
    assert extraction["employment_status"] == "salaried"
    assert extraction["collateral"] == "car"
    assert extraction["loan_type"] == "consumer"
    assert extraction["phone_number"] == "99112233"
    assert extraction["missing_fields"] == []
    assert "[REDACTED_PHONE]" in body["redacted_text"]
    assert 0 <= body["confidence"] <= 1


def test_extract_missing_income_term_and_phone_cases():
    no_income = client.post("/v1/extract", json={"text": MN_NO_INCOME}).json()["extraction"]
    assert "monthly_income" in no_income["missing_fields"]
    assert "loan_term_months" not in no_income["missing_fields"]
    assert "phone_number" not in no_income["missing_fields"]

    no_term = client.post("/v1/extract", json={"text": MN_NO_TERM}).json()["extraction"]
    assert "loan_term_months" in no_term["missing_fields"]
    assert "monthly_income" not in no_term["missing_fields"]

    no_phone = client.post(
        "/v1/extract",
        json={"text": "\u0411\u0438 6 \u0441\u0430\u044f \u0437\u044d\u044d\u043b 12 \u0441\u0430\u0440\u0430\u0430\u0440 \u0430\u0432\u043c\u0430\u0430\u0440 \u0431\u0430\u0439\u043d\u0430. \u041e\u0440\u043b\u043e\u0433\u043e 2 \u0441\u0430\u044f."},
    ).json()["extraction"]
    assert "phone_number" in no_phone["missing_fields"]


def test_rewrite_endpoint_returns_safer_alternatives():
    response = client.post(
        "/v1/rewrite",
        json={"text": MN_UNSAFE_APPROVAL, "target_language": "mn", "tone": "borrower_friendly"},
    )
    assert response.status_code == 200
    body = response.json()
    assert "guaranteed approval" in body["compliance_warnings"]
    assert body["safer_alternatives"]
    assert body["model"] == "Qwen3-32B-MN-Lendex"


def test_compliance_check_detects_unsafe_and_fee_wording():
    approval = client.post(
        "/v1/compliance-check",
        json={"text": MN_UNSAFE_APPROVAL, "language": "mn"},
    ).json()
    assert approval["is_safe"] is False
    assert approval["issues"][0]["category"] == "guaranteed approval"

    fees = client.post(
        "/v1/compliance-check",
        json={"text": MN_MISLEADING_FEES, "language": "mn"},
    ).json()
    assert fees["is_safe"] is False
    assert any(issue["category"] == "misleading interest/fee wording" for issue in fees["issues"])


def test_glossary_check_returns_terms_and_warnings():
    response = client.post(
        "/v1/glossary/check",
        json={"text": "loan interest rate fee collateral", "glossary_id": "lendex_finance"},
    )
    assert response.status_code == 200
    body = response.json()
    assert "\u0437\u044d\u044d\u043b" in body["terms_used"]
    assert body["glossary_warnings"]
    assert body["preferred_terms"]["loan"] == "\u0437\u044d\u044d\u043b"


def test_evaluate_endpoint_uses_teacher_model_by_default():
    response = client.post(
        "/v1/evaluate",
        json={
            "benchmark_name": "MongolianBankBench-v1",
            "items": [
                {
                    "id": "bank-approval-001",
                    "input": MN_APPROVAL_ASK,
                    "expected": "\u042d\u0446\u0441\u0438\u0439\u043d \u0448\u0438\u0439\u0434\u0432\u044d\u0440 \u0445\u044f\u043d\u0430\u043b\u0442\u044b\u043d \u0434\u0430\u0440\u0430\u0430 \u0433\u0430\u0440\u043d\u0430.",
                    "domain": "lending",
                }
            ],
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["judge_model"] == "Qwen3-235B-A22B-Instruct-2507"
    assert body["average_score"] == 0.8
    assert body["scores"][0]["item_id"] == "bank-approval-001"


def test_safe_log_text_redacts_all_supported_pii():
    raw = "99112233 \u0410\u041112345678 borrower@example.mn 123456789012"
    redacted = safe_log_text(raw)
    assert "99112233" not in redacted
    assert "\u0410\u041112345678" not in redacted
    assert "borrower@example.mn" not in redacted
    assert "123456789012" not in redacted
    assert "[REDACTED_PHONE]" in redacted
    assert "[REDACTED_EMAIL]" in redacted
    assert "[REDACTED_NUMBER]" in redacted
