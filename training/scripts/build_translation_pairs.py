from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True, help="JSONL with source_text, target_text, license metadata.")
    parser.add_argument("--output", type=Path, default=Path("datasets/processed/translation_pairs.jsonl"))
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.input.open("r", encoding="utf-8") as source, args.output.open("w", encoding="utf-8") as target:
        for line in source:
            item = json.loads(line)
            if not item.get("license_status") or not item.get("allowed_usage"):
                continue
            target.write(json.dumps({
                "messages": [
                    {"role": "system", "content": "Translate accurately between English and Mongolian."},
                    {"role": "user", "content": item["source_text"]},
                    {"role": "assistant", "content": item["target_text"]},
                ],
                "metadata": {key: item.get(key) for key in ["source_url", "license_status", "retrieval_date", "allowed_usage"]},
            }, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()
