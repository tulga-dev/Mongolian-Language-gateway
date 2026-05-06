import json
from pathlib import Path


DEFAULT_TERMS = {
    "loan": "зээл",
    "interest rate": "хүүгийн хувь",
    "fee": "шимтгэл",
    "collateral": "барьцаа",
    "approval": "зөвшөөрөл",
    "application": "зээлийн хүсэлт",
    "final review": "эцсийн хяналт",
}


class Glossary:
    def __init__(self, glossary_dir: Path):
        self.glossary_dir = glossary_dir

    def load(self, glossary_id: str | None = None) -> dict[str, str]:
        if not glossary_id:
            return DEFAULT_TERMS
        path = self.glossary_dir / f"{glossary_id}.json"
        if not path.exists():
            return DEFAULT_TERMS
        with path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
        return {**DEFAULT_TERMS, **data}

    def check(self, text: str, glossary_id: str | None = None) -> tuple[list[str], list[str], dict[str, str]]:
        glossary = self.load(glossary_id)
        lowered = text.lower()
        terms_used: list[str] = []
        warnings: list[str] = []
        for source, preferred in glossary.items():
            if source.lower() in lowered or preferred.lower() in lowered:
                terms_used.append(preferred)
            if source.lower() in lowered and preferred.lower() not in lowered:
                warnings.append(f"Use preferred Mongolian term '{preferred}' for '{source}'.")
        return sorted(set(terms_used)), warnings, glossary
