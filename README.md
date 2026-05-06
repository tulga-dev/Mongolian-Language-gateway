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

## Run Benchmarks

```powershell
python training/scripts/run_eval.py --benchmark datasets/benchmark/GeneralMongolianBench-v1.jsonl
python training/scripts/run_eval.py --benchmark datasets/benchmark/MongolianBankBench-v1.jsonl
```

The current evaluator is a placeholder heuristic. Production evaluation should call `Qwen3-235B-A22B-Instruct-2507` with the judge prompts in `training/evals/judge_prompts.py`.

## Lendex Integration

Lendex can call:

- `/v1/chat` for borrower support with polite `Та` wording and missing-field prompts
- `/v1/extract` for structured loan application extraction
- `/v1/compliance-check` before publishing or sending lending copy
- `/v1/rewrite` to produce safer Mongolian alternatives

Never rely on model output as final loan approval. Final approval must remain with the lender's review system.

## Datagate Integration

Datagate can call:

- `/v1/translate` for English <-> Mongolian content
- `/v1/glossary/check` to enforce financial/legal terminology
- `/v1/evaluate` to run benchmark suites during model promotion

For regulated workflows, keep request/response audit metadata while redacting borrower PII from logs.
