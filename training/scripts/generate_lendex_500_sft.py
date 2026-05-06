from __future__ import annotations

import argparse
import json
from pathlib import Path

OUTPUT = Path("datasets/processed/lendex_500_sft.jsonl")
DOMAINS = [
    "borrower_chat",
    "extraction",
    "compliance_rewrite",
    "finance_translation",
    "missing_field_clarification",
]
LOAN_TYPES = ["хэрэглээний", "бизнесийн", "орон сууцны", "автомашины", "эргэлтийн хөрөнгийн"]
AMOUNTS = ["3 сая", "5 сая", "8 сая", "10 сая", "12 сая", "15 сая", "20 сая", "25 сая", "30 сая", "50 сая"]
TERMS = ["6 сар", "9 сар", "12 сар", "18 сар", "24 сар", "36 сар", "48 сар", "60 сар", "3 жил", "5 жил"]
INCOMES = ["1.5 сая", "2 сая", "2.5 сая", "3 сая", "4 сая", "5 сая", "6 сая", "8 сая", "тогтмол бус", "улирлын"]
EMPLOYMENT = ["цалинтай", "хувиараа хөдөлмөр эрхэлдэг", "жижиг бизнес эрхэлдэг", "гэрээт ажилтай", "түр ажилтай"]
COLLATERAL = ["барьцаагүй", "автомашин", "орон сууц", "тоног төхөөрөмж", "агуулахын бараа"]
MISSING_FIELDS = ["сарын орлого", "зээлийн хугацаа", "холбоо барих утас", "ажил эрхлэлт", "барьцааны мэдээлэл"]
ENGLISH_TERMS = [
    ("loan application", "зээлийн хүсэлт"),
    ("interest rate", "хүүгийн хувь"),
    ("service fee", "үйлчилгээний шимтгэл"),
    ("collateral", "барьцаа"),
    ("final review", "эцсийн хяналт"),
]


def metadata(domain: str) -> dict:
    return {
        "domain": domain,
        "source": "synthetic_lendex_datagate_v1",
        "license_status": "synthetic",
        "allowed_usage": "training_allowed",
        "contains_pii": False,
    }


def record(identifier: int, domain: str, user: str, assistant: str) -> dict:
    return {
        "id": f"lendex-sft-{identifier:04d}",
        "messages": [
            {
                "role": "system",
                "content": (
                    "Та Lendex болон Datagate-д зориулсан монгол хэлний зээлийн туслах. "
                    "Та эелдэг, ойлгомжтой хариулж, зээлийн зөвшөөрөл амлахгүй."
                ),
            },
            {"role": "user", "content": user},
            {"role": "assistant", "content": assistant},
        ],
        **metadata(domain),
    }


def borrower_chat(i: int) -> tuple[str, str]:
    amount = AMOUNTS[i % len(AMOUNTS)]
    term = TERMS[(i * 2) % len(TERMS)]
    loan_type = LOAN_TYPES[(i * 3) % len(LOAN_TYPES)]
    user = f"Би {amount} төгрөгийн {loan_type} зээл {term} хугацаатай авах боломжтой юу?"
    assistant = (
        f"Та {amount} төгрөгийн {loan_type} зээлийн хүсэлтээ урьдчилан шалгуулж болно. "
        "Эцсийн шийдвэр нь орлого, ажил эрхлэлт, барьцаа болон байгууллагын хяналтын дараа гарна. "
        "Та сарын орлого, ажил эрхлэлт, барьцааны мэдээллээ нэмж өгнө үү."
    )
    return user, assistant


def extraction(i: int) -> tuple[str, str]:
    amount = AMOUNTS[(i + 1) % len(AMOUNTS)]
    term = TERMS[(i + 3) % len(TERMS)]
    income = INCOMES[(i + 5) % len(INCOMES)]
    employment = EMPLOYMENT[(i + 2) % len(EMPLOYMENT)]
    collateral = COLLATERAL[(i + 4) % len(COLLATERAL)]
    loan_type = LOAN_TYPES[(i + 1) % len(LOAN_TYPES)]
    user = (
        f"Дараах зээлийн хүсэлтийг JSON болгож бүтэцлэ: {amount} төгрөгийн {loan_type} зээл, "
        f"хугацаа {term}, сарын орлого {income}, ажил эрхлэлт {employment}, барьцаа {collateral}."
    )
    assistant = (
        "Та дараах бүтэцлэгдсэн мэдээллийг ашиглаж болно: "
        "{"
        f"\"loan_amount\":\"{amount}\","
        f"\"loan_term\":\"{term}\","
        f"\"monthly_income\":\"{income}\","
        f"\"employment_status\":\"{employment}\","
        f"\"collateral\":\"{collateral}\","
        f"\"loan_type\":\"{loan_type}\","
        "\"phone_number\":null,"
        "\"missing_fields\":[\"холбоо барих утас\"]"
        "}. Эцсийн шийдвэр зөвхөн нэмэлт хяналтын дараа гарна."
    )
    return user, assistant


def compliance_rewrite(i: int) -> tuple[str, str]:
    risky = [
        "Таны зээл заавал батална.",
        "Манай зээл хүү шимтгэлгүй хамгийн ашигтай.",
        "Та урьдчилан зөвшөөрөгдсөн тул санаа зовох зүйлгүй.",
        "Таны хүсэлт эцсийн байдлаар зөвшөөрөгдсөн.",
        "Татгалзсан шалтгаан нь та муу зээлдэгч.",
    ][i % 5]
    user = f"Энэ өгүүлбэрийг зээлийн compliance-safe хэлбэрт зас: {risky}"
    assistant = (
        "Та дараах аюулгүй хувилбарыг ашиглаж болно: "
        "Таны зээлийн хүсэлтийг урьдчилан шалгаж болох бөгөөд хүү, шимтгэл, нөхцөл нь бүтээгдэхүүн, "
        "шалгуур болон гэрээний нөхцлөөс хамаарна. Эцсийн шийдвэр нэмэлт хяналтын дараа гарна."
    )
    return user, assistant


def finance_translation(i: int) -> tuple[str, str]:
    english, mongolian = ENGLISH_TERMS[i % len(ENGLISH_TERMS)]
    amount = AMOUNTS[(i + 2) % len(AMOUNTS)]
    user = f"Translate to Mongolian for a lending workflow: Please review the {english} for a {amount} loan."
    assistant = (
        f"Та энэ өгүүлбэрийг ингэж орчуулж болно: {amount} төгрөгийн зээлийн {mongolian}-ийг хянана уу. "
        "Энэ орчуулга нь зээлийн зөвшөөрөл амлахгүй бөгөөд эцсийн хяналт шаардлагатайг хадгална."
    )
    return user, assistant


def missing_field_clarification(i: int) -> tuple[str, str]:
    field = MISSING_FIELDS[i % len(MISSING_FIELDS)]
    loan_type = LOAN_TYPES[(i + 4) % len(LOAN_TYPES)]
    user = f"{loan_type} зээлийн хүсэлтэд {field} дутуу байна. Харилцагчаас эелдгээр асуух мессеж бич."
    assistant = (
        f"Та {loan_type} зээлийн хүсэлтээ үргэлжлүүлэхийн тулд {field}-ийн мэдээллээ нэмж өгнө үү. "
        "Энэ мэдээлэл нь урьдчилсан шалгалтад ашиглагдах бөгөөд эцсийн шийдвэр нэмэлт хяналтын дараа гарна."
    )
    return user, assistant


BUILDERS = {
    "borrower_chat": borrower_chat,
    "extraction": extraction,
    "compliance_rewrite": compliance_rewrite,
    "finance_translation": finance_translation,
    "missing_field_clarification": missing_field_clarification,
}


def build_records(count: int) -> list[dict]:
    records = []
    for idx in range(count):
        domain = DOMAINS[idx % len(DOMAINS)]
        user, assistant = BUILDERS[domain](idx)
        records.append(record(idx + 1, domain, user, assistant))
    return records


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate synthetic Mongolian lending SFT examples.")
    parser.add_argument("--count", type=int, default=500)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()

    records = build_records(args.count)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as handle:
        for item in records:
            handle.write(json.dumps(item, ensure_ascii=False) + "\n")
    print(f"Wrote {len(records)} records to {args.output}")


if __name__ == "__main__":
    main()
