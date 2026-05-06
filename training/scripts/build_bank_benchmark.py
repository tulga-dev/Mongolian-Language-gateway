from __future__ import annotations

import argparse
import json
from pathlib import Path

TEMPLATE_ITEMS = [
    {"id": "bank-mn-001", "task": "compliance_rewrite", "input": "Таны зээл заавал батална.", "expected": "Таны хүсэлтийг банкны эцсийн хяналт, шаардлагын дагуу шийдвэрлэнэ.", "domain": "lending"},
    {"id": "bank-mn-002", "task": "borrower_chat", "input": "Би 10 сая төгрөгийн зээл авмаар байна. Ямар материал хэрэгтэй вэ?", "expected": "Зээлийн хүсэлт эцсийн хяналтын дараа шийдвэрлэгдэнэ.", "domain": "borrower_support"},
]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("datasets/benchmark/MongolianBankBench-v1.jsonl"))
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as handle:
        for item in TEMPLATE_ITEMS:
            item["metadata"] = {"license": "template", "compliance_review_required": True}
            handle.write(json.dumps(item, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()
