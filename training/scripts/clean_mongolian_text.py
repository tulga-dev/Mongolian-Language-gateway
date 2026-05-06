from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

CYRILLIC_OR_BASIC = re.compile(r"[А-Яа-яӨөҮүЁё0-9\s.,!?;:'\"()%\-/]+")
SPACE_RE = re.compile(r"\s+")


def clean_text(text: str) -> str:
    text = SPACE_RE.sub(" ", text).strip()
    return text


def looks_mongolian(text: str) -> bool:
    chars = CYRILLIC_OR_BASIC.findall(text)
    return sum(len(chunk) for chunk in chars) / max(len(text), 1) > 0.6


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.input.open("r", encoding="utf-8") as source, args.output.open("w", encoding="utf-8") as target:
        for line in source:
            item = json.loads(line)
            text = clean_text(item.get("text", ""))
            if text and looks_mongolian(text):
                item["text"] = text
                target.write(json.dumps(item, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()
