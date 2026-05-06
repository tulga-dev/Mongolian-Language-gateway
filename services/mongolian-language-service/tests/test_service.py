from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_compliance_detects_guaranteed_approval():
    response = client.post(
        "/v1/compliance-check",
        json={"text": "Таны зээл заавал батална.", "language": "mn"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["is_safe"] is False
    assert body["issues"][0]["category"] == "guaranteed approval"


def test_extract_redacts_phone_number():
    response = client.post(
        "/v1/extract",
        json={"text": "Би 5000000 төгрөг 12 сарын хугацаатай зээл авмаар байна. 99112233"},
    )
    assert response.status_code == 200
    body = response.json()
    assert "[REDACTED_PHONE]" in body["redacted_text"]
