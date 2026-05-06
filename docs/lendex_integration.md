# Lendex Integration

## Recommended Endpoints

- `/v1/chat`: borrower support chat
- `/v1/extract`: loan application extraction
- `/v1/rewrite`: safer Mongolian lending copy
- `/v1/compliance-check`: pre-send safety check
- `/v1/glossary/check`: terminology enforcement

## Borrower Chat Contract

The assistant must:

- Default to Mongolian
- Answer Mongolian users in Mongolian
- Answer English users in English
- Answer mixed text in the dominant language
- Use polite `Та` wording for borrowers
- Never promise loan approval
- Ask for missing loan application fields

Missing loan application fields:

- Loan amount
- Term
- Income
- Employment
- Collateral
- Loan type
- Phone number

## Compliance Guardrail

Run generated borrower-facing copy through `/v1/compliance-check` before display or delivery. High-risk outputs should be blocked or sent to human review.

## Logging

Do not log raw borrower PII. Use redacted text for request traces and analytics.
