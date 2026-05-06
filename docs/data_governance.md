# Data Governance

## Core Rules

- Do not train on copyrighted content unless licensed or otherwise allowed.
- Do not train on raw customer PII.
- Do not use Google Translate output as gold training data unless legal review approves it.
- Google Translate may be used only as a baseline or draft weak label before human review.
- Store `source_url`, `license_status`, `retrieval_date`, and `allowed_usage` for every document.

## Required Metadata

Every source document must include:

```json
{
  "source_url": "https://example.mn/document",
  "license_status": "open_license_verified",
  "retrieval_date": "2026-05-06",
  "allowed_usage": "training_allowed",
  "pii_status": "no_pii_detected",
  "review_status": "approved"
}
```

## Source Review

Before ingestion, review:

- License terms
- Robots.txt and terms of service
- Whether the content contains customer PII
- Whether the document is government/public sector text, public-domain text, licensed text, or merely publicly visible copyrighted content

Publicly visible does not automatically mean training is allowed.

## Borrower Data

Use synthetic, consented, or fully anonymized examples for borrower chat and extraction. Logs must redact phone numbers, email addresses, and register numbers before storage.

## Bank Websites

Khan Bank, TDB, Golomt Bank, XacBank, and State Bank websites should be treated as reference sources until usage rights are confirmed. Do not scrape aggressively. Prefer manually curated, licensed terminology lists and public product pages reviewed by legal.
