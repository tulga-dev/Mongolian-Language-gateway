# Datagate Integration

## Recommended Endpoints

- `/v1/translate`: English <-> Mongolian translation
- `/v1/glossary/check`: preferred financial/legal terminology
- `/v1/evaluate`: benchmark execution during release checks

## Translation Usage

For regulated content, set:

```json
{
  "domain": "finance",
  "tone": "formal",
  "compliance_sensitive": true,
  "require_human_review": true
}
```

## Model Promotion

Before promoting a new Qwen3-32B fine-tune:

1. Run `GeneralMongolianBench-v1`.
2. Run `MongolianBankBench-v1`.
3. Compare against the current production model.
4. Require human review for compliance-sensitive regressions.
5. Use `Qwen3-235B-A22B-Instruct-2507` as evaluator, not the student model.

## Audit Metadata

Store:

- Model name and version
- Prompt template version
- Glossary version
- Compliance check result
- Human review status where applicable
