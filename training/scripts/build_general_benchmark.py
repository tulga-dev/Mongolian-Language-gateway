from __future__ import annotations

import argparse
import json
from pathlib import Path

TEMPLATE_ITEMS = [
    {"id": "general-mn-001", "task": "fluency", "input": "Монгол хэлээр энгийн, найрсаг мэндчилгээ бич.", "expected": "Сайн байна уу? Танд энэ өдрийн мэнд хүргэе.", "domain": "general"},
    {"id": "general-mn-002", "task": "translation_en_mn", "input": "Please translate: The customer asked for more information.", "expected": "Харилцагч нэмэлт мэдээлэл хүссэн.", "domain": "general"},
]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("datasets/benchmark/GeneralMongolianBench-v1.jsonl"))
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as handle:
        for item in TEMPLATE_ITEMS:
            item["metadata"] = {"license": "template", "human_review_required": True}
            handle.write(json.dumps(item, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()
