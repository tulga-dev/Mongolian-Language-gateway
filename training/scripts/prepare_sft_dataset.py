from __future__ import annotations

import argparse
import json
import random
from pathlib import Path
from typing import Any

DEFAULT_INPUT = Path("datasets/processed/teacher_generated_lendex_sft.jsonl")
DEFAULT_TRAIN = Path("datasets/processed/sft_train.jsonl")
DEFAULT_VAL = Path("datasets/processed/sft_val.jsonl")
FALLBACK_SEEDS = Path("datasets/raw/finance/seed_prompts.example.jsonl")


def validate_messages(item: dict[str, Any]) -> None:
    messages = item.get("messages")
    if not isinstance(messages, list) or len(messages) < 2:
        raise ValueError(f"{item.get('id', '<missing id>')}: messages must contain at least user and assistant entries")
    roles = [message.get("role") for message in messages if isinstance(message, dict)]
    if "user" not in roles or "assistant" not in roles:
        raise ValueError(f"{item.get('id', '<missing id>')}: messages must include user and assistant roles")
    for message in messages:
        if message.get("role") not in {"system", "user", "assistant"}:
            raise ValueError(f"{item.get('id', '<missing id>')}: invalid role {message.get('role')}")
        if not isinstance(message.get("content"), str) or not message["content"].strip():
            raise ValueError(f"{item.get('id', '<missing id>')}: empty message content")


def fallback_records() -> list[dict[str, Any]]:
    with FALLBACK_SEEDS.open("r", encoding="utf-8") as handle:
        seeds = [json.loads(line) for line in handle if line.strip()]
    records = []
    for seed in seeds:
        records.append(
            {
                "id": f"fallback-{seed['id']}",
                "messages": [
                    {"role": "system", "content": "Answer safely in Mongolian for lending workflows."},
                    {"role": "user", "content": seed["prompt"]},
                    {
                        "role": "assistant",
                        "content": "Таны хүсэлтийг шалгаж болно. Эцсийн шийдвэр нь нэмэлт хяналтын дараа гарна.",
                    },
                ],
                "contains_pii": False,
                "source": "fallback_seed_for_local_prep",
            }
        )
    return records


def load_records(path: Path, allow_fallback: bool) -> list[dict[str, Any]]:
    if not path.exists():
        if allow_fallback:
            return fallback_records()
        raise FileNotFoundError(f"{path} does not exist. Run generate_teacher_data.py first.")
    with path.open("r", encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate and split SFT messages JSONL.")
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--train-output", type=Path, default=DEFAULT_TRAIN)
    parser.add_argument("--val-output", type=Path, default=DEFAULT_VAL)
    parser.add_argument("--val-ratio", type=float, default=0.1)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--allow-pii", action="store_true")
    parser.add_argument("--allow-small", action="store_true", help="Allow small local prep datasets and fallback seeds.")
    args = parser.parse_args()

    records = load_records(args.input, allow_fallback=args.allow_small)
    accepted: list[dict[str, Any]] = []
    rejected = 0
    for record in records:
        validate_messages(record)
        if record.get("contains_pii") is True and not args.allow_pii:
            rejected += 1
            continue
        accepted.append(record)

    if not accepted:
        raise SystemExit("No SFT records accepted after validation/PII filtering.")
    if len(accepted) < 20 and not args.allow_small:
        raise SystemExit("Dataset is too small for training prep. Pass --allow-small for smoke tests.")

    rng = random.Random(args.seed)
    rng.shuffle(accepted)
    val_count = max(1, int(len(accepted) * args.val_ratio)) if len(accepted) > 1 else 0
    val_records = accepted[:val_count]
    train_records = accepted[val_count:] or accepted

    args.train_output.parent.mkdir(parents=True, exist_ok=True)
    args.val_output.parent.mkdir(parents=True, exist_ok=True)
    with args.train_output.open("w", encoding="utf-8") as train_handle:
        for record in train_records:
            train_handle.write(json.dumps(record, ensure_ascii=False) + "\n")
    with args.val_output.open("w", encoding="utf-8") as val_handle:
        for record in val_records:
            val_handle.write(json.dumps(record, ensure_ascii=False) + "\n")

    print(json.dumps({
        "accepted": len(accepted),
        "rejected_contains_pii": rejected,
        "train": len(train_records),
        "validation": len(val_records),
        "train_output": str(args.train_output),
        "val_output": str(args.val_output),
    }, indent=2))


if __name__ == "__main__":
    main()
