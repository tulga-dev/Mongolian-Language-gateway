# Mongolian Language Factory

Infrastructure to train, evaluate, and serve a Mongolian-native Qwen model for Lendex and Datagate.

## Model Strategy

- Teacher/evaluator: `Qwen3-235B-A22B-Instruct-2507`
- Production student: `Qwen3-32B`
- Primary model family: Qwen
- Gemma is not used as the primary model.

The factory targets:

- General Mongolian fluency
- English <-> Mongolian translation
- Mongolian borrower chat
- Financial and legal terminology
- Loan application extraction
- Compliance-safe lending wording

## Repository Layout

```text
datasets/                         Raw, processed, and benchmark data
services/mongolian-language-service FastAPI serving layer
training/configs/                 Qwen training configuration placeholders
training/scripts/                 Dataset and benchmark builders
training/evals/                   Evaluation scoring helpers and judge prompts
docs/                             Governance, benchmark, and integration specs
```

## Setup

```powershell
cd mongolian-language-factory
Copy-Item .env.example .env
cd services/mongolian-language-service
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
```

## Environment Variables

Copy `.env.example` to `.env` and configure:

- `MODEL_PROVIDER`: `mock`, `openai`, or `vllm`
- `PRODUCTION_MODEL`: production Qwen3-32B student model name
- `TEACHER_MODEL`: Qwen3-235B-A22B-Instruct-2507 evaluator model name
- `OPENAI_BASE_URL`, `OPENAI_API_KEY`: OpenAI-compatible hosted endpoint
- `VLLM_BASE_URL`, `VLLM_API_KEY`: local or remote vLLM endpoint
- `REDIS_URL`: cache endpoint
- `DATABASE_URL`: metadata/event database endpoint
- `GLOSSARY_DIR`: JSON glossary directory

## Run API Locally

Python:

```powershell
cd services/mongolian-language-service
uvicorn app.main:app --reload --host 0.0.0.0 --port 8080
```

Docker:

```powershell
cd mongolian-language-factory
docker compose up --build
```

Health check:

```powershell
Invoke-RestMethod http://localhost:8080/health
```

## Run Tests

From the repository root:

```powershell
python -m compileall services training
cd services/mongolian-language-service
pip install -e ".[dev]"
pytest
```

The test suite uses the mock Qwen-compatible provider by default, so it does not train a model, scrape websites, or require a live OpenAI/vLLM endpoint.

## API Endpoints

- `GET /health`
- `POST /v1/translate`
- `POST /v1/chat`
- `POST /v1/extract`
- `POST /v1/rewrite`
- `POST /v1/compliance-check`
- `POST /v1/glossary/check`
- `POST /v1/evaluate`

## Add Datasets

1. Add candidate sources through `training/scripts/collect_sources.py`.
2. Record `source_url`, `license_status`, `retrieval_date`, and `allowed_usage` for every document.
3. Exclude copyrighted content unless licensed or legally allowed.
4. Exclude raw customer PII. Use redaction and synthetic examples for borrower flows.
5. Do not treat Google Translate output as gold training data unless legal review approves it. It may be used only as a baseline or weak draft label before human review.

Create the source manifest:

```powershell
python training/scripts/collect_sources.py --output datasets/processed/source_manifest.jsonl
```

Fetching is disabled by default. Any source-specific fetcher must respect robots.txt, licensing, and rate limits.

## Build SFT v2 Dataset

Generate the higher-quality Mongolian credit analyst SFT v2 dataset and run regression quality checks:

```bash
python training/scripts/build_lendex_sft_v2.py
python training/scripts/check_sft_v2_quality.py datasets/processed/sft_v2_train.jsonl
python training/scripts/check_sft_v2_quality.py datasets/processed/sft_v2_val.jsonl
wc -l datasets/processed/sft_v2_train.jsonl datasets/processed/sft_v2_val.jsonl
```

The v2 generator creates structured Lendex/DataGate examples for credit memo writing, risk classification, ratio explanation, application summaries, collateral assessment, repayment capacity, red flags, lender recommendations, financial statement summaries, and cash-flow lending decisions. It does not train a model.

## Run Benchmarks

```powershell
python training/scripts/run_eval.py --benchmark datasets/benchmark/GeneralMongolianBench-v1.jsonl
python training/scripts/run_eval.py --benchmark datasets/benchmark/MongolianBankBench-v1.jsonl
```

The current evaluator is a placeholder heuristic. Production evaluation should call `Qwen3-235B-A22B-Instruct-2507` with the judge prompts in `training/evals/judge_prompts.py`.

## Smoke Test Trained LoRA Adapter

After training `Qwen/Qwen3-32B` with the Lendex/DataGate LoRA adapter on a CUDA GPU, run:

```bash
export HF_HOME=/workspace/hf-cache
export HUGGINGFACE_HUB_CACHE=/workspace/hf-cache/hub

python training/scripts/smoke_infer_qwen3_32b_lora.py \
  --base-model Qwen/Qwen3-32B \
  --adapter outputs/qwen3_32b_mn_lendex_lora \
  --max-new-tokens 512
```

The smoke script loads the base model in 4-bit mode, attaches the LoRA adapter, runs Mongolian Lendex/DataGate prompts, and prints each prompt with the generated answer separated by clear divider lines. It does not retrain the model.

## Lendex Integration

Lendex can call:

- `/v1/chat` for borrower support with polite `Та` wording and missing-field prompts
- `/v1/extract` for structured loan application extraction
- `/v1/compliance-check` before publishing or sending lending copy
- `/v1/rewrite` to produce safer Mongolian alternatives

Never rely on model output as final loan approval. Final approval must remain with the lender's review system.

Recommended borrower chat flow:

1. Send recent borrower messages to `/v1/chat` with any known `borrower_context`.
2. Read `missing_application_fields` and ask the borrower only for missing values.
3. Run any outgoing lending copy through `/v1/compliance-check`.
4. Send compliance-sensitive responses to human review when `compliance_warnings` is non-empty or confidence is low.

Recommended extraction flow:

1. Send borrower free text to `/v1/extract`.
2. Store structured fields: `loan_amount`, `loan_term_months`, `monthly_income`, `employment_status`, `collateral`, `loan_type`, and `phone_number`.
3. Use `missing_fields` to continue the application intake.
4. Log only `redacted_text`; never log raw phone numbers, register numbers, email addresses, or borrower PII.

## Datagate Integration

Datagate can call:

- `/v1/translate` for English <-> Mongolian content
- `/v1/glossary/check` to enforce financial/legal terminology
- `/v1/evaluate` to run benchmark suites during model promotion

For regulated workflows, keep request/response audit metadata while redacting borrower PII from logs.

After OCR or document parsing:

1. Normalize OCR text and remove obvious parsing artifacts before calling the service.
2. Call `/v1/extract` for loan application fields when the document contains borrower intent or application data.
3. Call `/v1/translate` when Datagate needs English <-> Mongolian document text.
4. Call `/v1/glossary/check` for financial/legal terminology before sending text downstream.
5. Keep OCR source metadata, parser version, model version, confidence, and compliance-check results for audit.
6. Do not use parsed customer documents as training data unless consent, licensing, PII controls, and legal review explicitly allow it.
