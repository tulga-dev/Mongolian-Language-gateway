from __future__ import annotations

import argparse
import json
from pathlib import Path

DEFAULT_INPUT = Path("datasets/raw/finance/seed_prompts.example.jsonl")
DEFAULT_OUTPUT = Path("datasets/processed/teacher_generated_lendex_sft.jsonl")


def safe_answer(prompt: str) -> str:
    return (
        "Таны хүсэлтийг хүлээн авлаа. Зээлийн боломжийг шалгахын тулд зээлийн хэмжээ, "
        "хугацаа, сарын орлого, ажил эрхлэлт, барьцаа, зээлийн төрөл болон холбоо барих "
        "утасны дугаарыг бүрэн өгнө үү. Эцсийн шийдвэр нь нэмэлт хяналт, байгууллагын "
        "шаардлагын дараа гарна."
        f"\n\nДаалгаврын агуулга: {prompt}"
    )


def iter_seed_prompts(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def build_record(seed: dict) -> dict:
    return {
        "id": f"teacher-{seed['id']}",
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are Qwen3-235B-A22B-Instruct-2507 generating safe Mongolian lending "
                    "SFT data for Lendex and Datagate. Never promise loan approval."
                ),
            },
            {"role": "user", "content": seed["prompt"]},
            {"role": "assistant", "content": safe_answer(seed["prompt"])},
        ],
        "domain": seed.get("domain", "lending"),
        "language": seed.get("language", "mn"),
        "contains_pii": bool(seed.get("contains_pii", False)),
        "source": "mock_teacher_dry_run",
        "model": "mock:Qwen3-235B-A22B-Instruct-2507",
        "license_status": "synthetic_seed",
        "allowed_usage": "training_allowed_after_human_review",
        "human_review_required": True,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate mock teacher SFT data from seed prompts.")
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--dry-run", action="store_true", help="Validate and print summary without writing.")
    args = parser.parse_args()

    seeds = iter_seed_prompts(args.input)
    records = [build_record(seed) for seed in seeds]

    if args.dry_run:
        print(json.dumps({"input": str(args.input), "output": str(args.output), "records": len(records)}, indent=2))
        return

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")
    print(f"Wrote {len(records)} teacher records to {args.output}")


if __name__ == "__main__":
    main()
