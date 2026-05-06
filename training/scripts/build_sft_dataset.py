from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True, help="Curated JSONL instruction examples.")
    parser.add_argument("--output", type=Path, default=Path("datasets/processed/mn_instruction_sft.jsonl"))
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.input.open("r", encoding="utf-8") as source, args.output.open("w", encoding="utf-8") as target:
        for line in source:
            item = json.loads(line)
            if item.get("contains_raw_customer_pii"):
                continue
            if item.get("google_translate_gold") is True:
                continue
            target.write(json.dumps(item, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()
