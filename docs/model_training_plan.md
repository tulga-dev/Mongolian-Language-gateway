# Model Training Plan

## Model Decision

- Primary family: Qwen
- Teacher/evaluator: `Qwen3-235B-A22B-Instruct-2507`
- Production student: `Qwen3-32B`
- Gemma is not the primary model.

## Stages

1. Continued pretraining on licensed/open Mongolian text.
2. SFT on curated Mongolian instruction data.
3. Lendex finance specialization for borrower chat, terminology, extraction, and compliance wording.
4. DPO or ORPO preference tuning with safe lending pairs.

## Continued Pretraining

Use `training/configs/qwen3_32b_mn_general_lora.yaml`.

Inputs:

- Mongolian Wikipedia dumps where license obligations are met
- OSCAR/CC100 Mongolian subsets where usage rights are confirmed
- Public government/legal texts after legal review
- Public-domain texts and public library metadata where rights allow

## SFT

Use curated examples for:

- Mongolian fluency
- English <-> Mongolian translation
- Borrower support
- Financial/legal terminology
- Loan application extraction
- Compliance-safe lending rewrite

## Finance Specialization

Use `training/configs/qwen3_32b_mn_lendex_lora.yaml`.

Create reviewed examples for:

- Polite borrower-facing `Та` responses
- Missing-field prompts
- No approval promises
- Interest, fee, collateral, term, and eligibility explanations

## Preference Tuning

Use `training/configs/qwen3_32b_mn_dpo.yaml`.

Chosen responses should be:

- Native Mongolian
- Clear and polite
- Terminology-compliant
- Lending-compliance safe
- Honest about final review

Rejected responses should include:

- Guaranteed approval claims
- Unsafe rejection explanations
- Misleading interest/fee wording
- Missing final review disclaimers
