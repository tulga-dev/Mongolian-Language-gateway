from __future__ import annotations

import argparse
import json
from pathlib import Path

TRAIN_OUTPUT = Path("datasets/processed/sft_v3_train.jsonl")
VAL_OUTPUT = Path("datasets/processed/sft_v3_val.jsonl")

DOMAIN_COUNTS = {
    "credit_memo_numeric": 500,
    "repayment_capacity_numeric": 300,
    "lender_recommendation_numeric": 250,
    "financial_ratios_numeric": 200,
    "risk_classification_structured": 150,
    "missing_documents_request": 100,
}

SECTORS = [
    "хүнсний бөөний худалдаа",
    "барилгын материалын худалдаа",
    "эмийн сан",
    "тээвэр ложистик",
    "оёдлын үйлдвэрлэл",
    "жижиг ресторан",
    "сэлбэгийн худалдаа",
    "сүү, сүүн бүтээгдэхүүний түгээлт",
    "цахилгаан барааны дэлгүүр",
    "хөдөө аж ахуйн тоног төхөөрөмжийн худалдаа",
]
DOC_SETS = [
    ["Дансны хуулга", "Татварын тайлан", "Зээлийн түүх", "Барьцааны үнэлгээ"],
    ["Дансны хуулга", "Татварын тайлан", "Үндсэн гэрээ", "Барьцааны үнэлгээ"],
    ["Дансны хуулга", "Зээлийн түүх", "Борлуулалтын гэрээ", "Барьцааны үнэлгээ"],
    ["Татварын тайлан", "Дансны хуулга", "Бараа материалын жагсаалт", "Зээлийн түүх"],
]


def scenario(index: int) -> dict:
    revenue = 60 + (index % 15) * 12
    expense_rates = [0.48, 0.55, 0.62, 0.70, 0.82]
    expense = round(revenue * expense_rates[index % len(expense_rates)])
    debt = 10 + (index % 12) * 9
    cash = 4 + (index % 10) * 4
    loan_amount = 12 + (index % 13) * 6
    term_months = [6, 9, 12, 18, 24, 30, 36][index % 7]
    return {
        "sector": SECTORS[index % len(SECTORS)],
        "revenue": revenue,
        "expense": expense,
        "debt": debt,
        "cash": cash,
        "loan_amount": loan_amount,
        "term_months": term_months,
        "docs": DOC_SETS[index % len(DOC_SETS)],
    }


def safe_div(numerator: float, denominator: float) -> float | None:
    if denominator == 0:
        return None
    return numerator / denominator


def percent(value: float | None) -> str:
    if value is None:
        return "тооцох боломжгүй"
    return f"{value * 100:.1f}%"


def money(value: float) -> str:
    if abs(value - round(value)) < 0.01:
        return f"₮{int(round(value))} сая"
    return f"₮{value:.1f} сая"


def calculate(data: dict) -> dict:
    profit = data["revenue"] - data["expense"]
    return {
        "profit": profit,
        "profit_margin": safe_div(profit, data["revenue"]),
        "expense_ratio": safe_div(data["expense"], data["revenue"]),
        "debt_to_revenue": safe_div(data["debt"], data["revenue"]),
        "cash_to_debt": safe_div(data["cash"], data["debt"]),
        "repayment": safe_div(data["loan_amount"], data["term_months"]),
    }


def risk_level(calc: dict) -> str:
    margin = calc["profit_margin"] or 0
    debt_ratio = calc["debt_to_revenue"] or 99
    cash_ratio = calc["cash_to_debt"] or 0
    if margin >= 0.30 and debt_ratio <= 0.45 and cash_ratio >= 0.30:
        return "Бага"
    if margin >= 0.15 and debt_ratio <= 0.85 and cash_ratio >= 0.12:
        return "Дунд"
    return "Өндөр"


def recommendation(calc: dict, level: str) -> str:
    margin = calc["profit_margin"] or 0
    debt_ratio = calc["debt_to_revenue"] or 99
    if level == "Бага":
        return "Нөхцөлтэй зөвшөөрөх боломжтой"
    if level == "Дунд" and margin >= 0.20:
        return "Нэмэлт баримт шаардлагатай"
    if debt_ratio > 0.9:
        return "Зээлийн дүнг бууруулах саналтай"
    return "Одоогоор зээл олгохгүй байх саналтай"


def prompt_for(data: dict, task: str) -> str:
    return (
        f"{task}: Салбар {data['sector']}. Орлого {data['revenue']} сая, "
        f"зардал {data['expense']} сая, өр төлбөр {data['debt']} сая, "
        f"мөнгөн үлдэгдэл {data['cash']} сая, хүссэн зээл {data['loan_amount']} сая, "
        f"хугацаа {data['term_months']} сар."
    )


def documents_block(data: dict) -> str:
    return "\n".join(f"- {doc}" for doc in data["docs"])


def strict_numeric_answer(data: dict, *, focus: str) -> str:
    calc = calculate(data)
    level = risk_level(calc)
    advice = recommendation(calc, level)
    repayment_line = ""
    if calc["repayment"] is not None:
        repayment_line = f"\n- Сарын төлбөрийн ойролцоо тооцоо: {money(calc['repayment'])}"
    return (
        "Зээлийн товч үнэлгээ\n\n"
        f"Эрсдэлийн түвшин: {level}\n\n"
        "Санхүүгийн тооцоолол:\n"
        f"- Орлого: {money(data['revenue'])}\n"
        f"- Зардал: {money(data['expense'])}\n"
        f"- Тооцоолсон ашиг: {money(calc['profit'])}\n"
        f"- Ашгийн маржин: {percent(calc['profit_margin'])}\n"
        f"- Зардлын харьцаа: {percent(calc['expense_ratio'])}\n"
        f"- Өр/орлогын харьцаа: {percent(calc['debt_to_revenue'])}\n"
        f"- Мөнгө/өрийн харьцаа: {percent(calc['cash_to_debt'])}"
        f"{repayment_line}\n\n"
        "Үнэлгээ:\n"
        f"{focus} Орлого, зардлын бүтэц, өрийн дарамт, хөрвөх чадвар зэрэг үзүүлэлтээр санхүүгийн бүтэц дүгнэгдэв. "
        "Мөнгөн үлдэгдэл нь богино хугацааны төлбөрийн чадварт шууд нөлөөлөх тул дансны бодит эргэлтээр баталгаажуулах шаардлагатай.\n\n"
        "Зөвлөмж:\n"
        f"{advice}. Эцсийн шийдвэрийг баталгаажсан баримт, бодлогын шалгуур, зээлийн хорооны хяналтын дараа гаргана.\n\n"
        "Дутуу баримт:\n"
        f"{documents_block(data)}"
    )


def ratio_answer(data: dict) -> str:
    calc = calculate(data)
    return (
        "Санхүүгийн харьцааны тайлбар\n\n"
        f"- Тооцоолсон ашиг: {money(calc['profit'])} буюу орлогоос зардлыг хассан дүн.\n"
        f"- Ашгийн маржин: {percent(calc['profit_margin'])}; үйл ажиллагааны ашигт ажиллагааг харуулна.\n"
        f"- Зардлын харьцаа: {percent(calc['expense_ratio'])}; зардлын сахилга бат болон ашигт дарамтыг үнэлнэ.\n"
        f"- Өр/орлогын харьцаа: {percent(calc['debt_to_revenue'])}; өрийн дарамт орлоготой харьцуулахад ямар түвшинд байгааг харуулна.\n"
        f"- Мөнгө/өрийн харьцаа: {percent(calc['cash_to_debt'])}; хөрвөх чадвар богино хугацааны өрийг даах эсэхийг харуулна.\n\n"
        "Эрсдэлийн түвшин: "
        f"{risk_level(calc)}. Та эдгээр тооцоог дансны хуулга, татварын тайлан, зээлийн түүхтэй тулган баталгаажуулна уу."
    )


def risk_answer(data: dict) -> str:
    calc = calculate(data)
    level = risk_level(calc)
    return (
        f"Эрсдэлийн түвшин: {level}\n\n"
        "Үндэслэл:\n"
        f"- Ашгийн маржин {percent(calc['profit_margin'])}, өр/орлогын харьцаа {percent(calc['debt_to_revenue'])}, "
        f"мөнгө/өрийн харьцаа {percent(calc['cash_to_debt'])} байна.\n"
        "- Санхүүгийн бүтэц, өрийн дарамт, хөрвөх чадварын үзүүлэлтүүдийг хамтад нь авч үзэхэд шийдвэрийг шууд батлах бус нэмэлт баталгаажуулалт шаардлагатай.\n\n"
        "Практик алхам:\n"
        f"{recommendation(calc, level)}. Дутуу баримтад {', '.join(data['docs'])} орно."
    )


def missing_docs_answer(data: dict) -> str:
    return (
        "Дутуу баримтын хүсэлт\n\n"
        "Та зээлийн хүсэлтийг бүрэн үнэлүүлэхийн тулд дараах баримтыг ирүүлнэ үү:\n"
        f"{documents_block(data)}\n\n"
        "Эдгээр баримт нь орлого, өрийн дарамт, хөрвөх чадвар, барьцааны үнэлгээг баталгаажуулахад ашиглагдана. "
        "Баримт бүрдсэний дараа эрсдэлийн түвшин болон зөвлөмжийг дахин шинэчилнэ."
    )


def build_example(domain: str, index: int) -> dict:
    data = scenario(index)
    if domain == "credit_memo_numeric":
        user = prompt_for(data, "Богино credit memo бич")
        assistant = strict_numeric_answer(data, focus="Зээлийн memo-д өгөгдсөн бүх тоог ашиглан тооцоо хийв.")
    elif domain == "repayment_capacity_numeric":
        user = prompt_for(data, "Төлбөрийн чадварыг тооцоотой үнэл")
        assistant = strict_numeric_answer(data, focus="Төлбөрийн чадварыг ашиг, сарын төлбөр, өрийн дарамтаар үнэлэв.")
    elif domain == "lender_recommendation_numeric":
        user = prompt_for(data, "Зээлдүүлэгчийн шийдвэрийн санал бич")
        assistant = strict_numeric_answer(data, focus="Зээлдүүлэгчийн санал нь тооцоолсон ашиг ба хөрвөх чадварт үндэслэв.")
    elif domain == "financial_ratios_numeric":
        user = prompt_for(data, "Санхүүгийн гол харьцааг тайлбарла")
        assistant = ratio_answer(data)
    elif domain == "risk_classification_structured":
        user = prompt_for(data, "Зээлдэгчийн эрсдэлийг бүтэцтэй ангил")
        assistant = risk_answer(data)
    elif domain == "missing_documents_request":
        user = prompt_for(data, "Дутуу баримтыг эелдгээр хүс")
        assistant = missing_docs_answer(data)
    else:
        raise ValueError(f"Unknown domain: {domain}")
    return {
        "id": f"lendex-v3-{domain}-{index:05d}",
        "messages": [
            {
                "role": "system",
                "content": (
                    "Та Lendex болон Datagate-д зориулсан монгол хэлтэй зээлийн шинжээч. "
                    "Зөвхөн эцсийн хариу бич. Тооцоог өгөгдсөн тооноос гарга. Дотоод бодол бүү харуул."
                ),
            },
            {"role": "user", "content": user},
            {"role": "assistant", "content": assistant},
        ],
        "metadata": {
            "domain": domain,
            "source": "synthetic_lendex_credit_analyst_v3",
            "license_status": "synthetic",
            "allowed_usage": "training_allowed",
            "contains_pii": False,
            "numeric_example": domain != "missing_documents_request",
        },
    }


def split_records(records: list[dict]) -> tuple[list[dict], list[dict]]:
    train: list[dict] = []
    val: list[dict] = []
    cursor = 0
    for domain, count in DOMAIN_COUNTS.items():
        domain_records = records[cursor : cursor + count]
        cursor += count
        split = int(count * 0.9)
        train.extend(domain_records[:split])
        val.extend(domain_records[split:])
    return train, val


def write_jsonl(path: Path, records: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def build_records() -> list[dict]:
    records: list[dict] = []
    global_index = 1
    for domain, count in DOMAIN_COUNTS.items():
        for _ in range(count):
            records.append(build_example(domain, global_index))
            global_index += 1
    return records


def main() -> None:
    parser = argparse.ArgumentParser(description="Build strict Lendex/DataGate SFT v3 dataset.")
    parser.add_argument("--train-output", type=Path, default=TRAIN_OUTPUT)
    parser.add_argument("--val-output", type=Path, default=VAL_OUTPUT)
    args = parser.parse_args()

    records = build_records()
    train, val = split_records(records)
    write_jsonl(args.train_output, train)
    write_jsonl(args.val_output, val)
    print(json.dumps({
        "total": len(records),
        "train": len(train),
        "validation": len(val),
        "train_output": str(args.train_output),
        "val_output": str(args.val_output),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
