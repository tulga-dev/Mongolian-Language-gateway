# Benchmark Spec

## GeneralMongolianBench-v1

Purpose:

- General Mongolian fluency
- Natural phrasing
- English <-> Mongolian translation
- Instruction following

Format:

```json
{
  "id": "general-mn-001",
  "task": "fluency",
  "input": "Монгол хэлээр энгийн, найрсаг мэндчилгээ бич.",
  "expected": "Сайн байна уу? Танд энэ өдрийн мэнд хүргэе.",
  "domain": "general",
  "metadata": {
    "language": "mn",
    "license": "template"
  }
}
```

## MongolianBankBench-v1

Purpose:

- Borrower chat quality
- Compliance-safe lending wording
- Financial/legal terminology
- Loan application extraction
- No loan approval promises

Required test categories:

- `compliance_rewrite`
- `borrower_chat`
- `loan_extraction`
- `translation_en_mn`
- `translation_mn_en`
- `glossary_enforcement`

## Evaluation

Use `Qwen3-235B-A22B-Instruct-2507` as a teacher/evaluator model. The judge should return JSON with:

- `score`: 0 to 1
- `issues`: list of fluency, terminology, compliance, or extraction issues
- `rationale`: concise explanation
- `safer_mongolian_alternative`: required for compliance failures

The placeholder `run_eval.py` uses heuristic scoring only until the evaluator endpoint is connected.
