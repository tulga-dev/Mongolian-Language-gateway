from __future__ import annotations

import argparse
import json
from pathlib import Path

TRAIN_OUTPUT = Path("datasets/processed/sft_v2_train.jsonl")
VAL_OUTPUT = Path("datasets/processed/sft_v2_val.jsonl")
TASKS = [
    "credit_memo",
    "borrower_risk_classification",
    "financial_ratio_explanation",
    "loan_application_summary",
    "collateral_assessment",
    "repayment_capacity_analysis",
    "red_flag_detection",
    "lender_recommendation",
    "financial_statement_summary",
    "cash_flow_lending_decision",
]
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
COLLATERALS = [
    ("агуулахын үл хөдлөх хөрөнгө", 180),
    ("ачааны автомашин", 95),
    ("орон сууц", 220),
    ("үйлдвэрийн тоног төхөөрөмж", 130),
    ("борлуулах бараа материал", 70),
]
MISSING_DOCS = [
    "сүүлийн 12 сарын дансны хуулга",
    "татварын тайлан",
    "зээлийн зориулалтын дэлгэрэнгүй тайлбар",
    "барьцааны үнэлгээний тайлан",
    "үндсэн харилцагчдын гэрээ",
]


def scenario(index: int) -> dict:
    revenue = 80 + (index % 11) * 18
    expense = int(revenue * (0.52 + (index % 5) * 0.05))
    debt = 20 + (index % 9) * 12
    cash = 6 + (index % 8) * 5
    loan_amount = 15 + (index % 10) * 8
    term_months = [6, 9, 12, 18, 24, 36][index % 6]
    collateral, collateral_value = COLLATERALS[index % len(COLLATERALS)]
    return {
        "sector": SECTORS[index % len(SECTORS)],
        "revenue": revenue,
        "expense": expense,
        "debt": debt,
        "cash": cash,
        "loan_amount": loan_amount,
        "term_months": term_months,
        "collateral": collateral,
        "collateral_value": collateral_value,
        "missing_doc": MISSING_DOCS[index % len(MISSING_DOCS)],
    }


def metrics(data: dict) -> dict:
    profit = data["revenue"] - data["expense"]
    repayment = data["loan_amount"] / data["term_months"]
    return {
        "profit": profit,
        "profit_margin": profit / data["revenue"],
        "debt_to_revenue": data["debt"] / data["revenue"],
        "cash_to_debt": data["cash"] / data["debt"],
        "expense_ratio": data["expense"] / data["revenue"],
        "monthly_repayment": repayment,
        "collateral_coverage": data["collateral_value"] / data["loan_amount"],
    }


def risk_level(data: dict, calc: dict) -> str:
    if calc["profit_margin"] >= 0.28 and calc["debt_to_revenue"] <= 0.45 and calc["cash_to_debt"] >= 0.25:
        return "Бага"
    if calc["profit_margin"] >= 0.15 and calc["debt_to_revenue"] <= 0.8:
        return "Дунд"
    return "Өндөр"


def money(value: float) -> str:
    if abs(value - round(value)) < 0.01:
        return f"{int(round(value))} сая"
    return f"{value:.1f} сая"


def percent(value: float) -> str:
    return f"{value * 100:.1f}%"


def base_input(data: dict) -> str:
    return (
        f"Салбар: {data['sector']}; орлого {data['revenue']} сая; зардал {data['expense']} сая; "
        f"өр төлбөр {data['debt']} сая; мөнгөн үлдэгдэл {data['cash']} сая; "
        f"хүссэн зээл {data['loan_amount']} сая; хугацаа {data['term_months']} сар; "
        f"барьцаа: {data['collateral']} ({data['collateral_value']} сая үнэлгээтэй)."
    )


def recommendation(level: str) -> str:
    if level == "Бага":
        return "Санал: нөхцөлтэй зөвшөөрөх боломжтой, баримтын бүрдлийг баталгаажуулсны дараа шийдвэрлэнэ."
    if level == "Дунд":
        return "Санал: нэмэлт баримт, мөнгөн урсгалын баталгаажуулалт хийсний дараа хязгаартай дүнгээр авч үзнэ."
    return "Санал: одоогийн нөхцөлөөр шууд зөвшөөрөхгүй, эрсдэлийг бууруулах нэмэлт баталгаа шаардлагатай."


def memo_body(data: dict) -> tuple[str, str]:
    calc = metrics(data)
    level = risk_level(data, calc)
    response = (
        "Зээлийн товч memo\n"
        f"- Эрсдэлийн түвшин: {level}\n"
        f"- Ашиг: {money(calc['profit'])}; ашгийн маржин: {percent(calc['profit_margin'])}; "
        f"өр/орлого: {percent(calc['debt_to_revenue'])}; мөнгө/өр: {percent(calc['cash_to_debt'])}.\n"
        f"- Сарын ойролцоо төлөлт: {money(calc['monthly_repayment'])}; барьцааны бүрхэлт: {calc['collateral_coverage']:.2f}x.\n"
        f"- Шийдвэрийн үндэслэл: {data['sector']} бизнесийн орлого, зардлын бүтэц болон одоогийн өрийн ачааллыг хамтад нь харгалзав.\n"
        f"- Дутуу баримт: {data['missing_doc']}.\n"
        f"- {recommendation(level)} Эцсийн шийдвэр нэмэлт хяналтын дараа гарна."
    )
    return f"Доорх мэдээлэл дээр үндэслэн богино credit memo бич: {base_input(data)}", response


def risk_classification(data: dict) -> tuple[str, str]:
    calc = metrics(data)
    level = risk_level(data, calc)
    response = (
        f"Эрсдэлийн ангилал: {level}\n"
        f"- Ашгийн маржин {percent(calc['profit_margin'])}, зардлын харьцаа {percent(calc['expense_ratio'])}, "
        f"өр/орлого {percent(calc['debt_to_revenue'])} байна.\n"
        f"- Мөнгөн үлдэгдэл/өрийн харьцаа {percent(calc['cash_to_debt'])} тул богино хугацааны дарамтыг тусгайлан шалгана.\n"
        f"- Дутуу баримт: {data['missing_doc']}.\n"
        f"- Та шийдвэр гаргахаас өмнө дансны бодит эргэлт болон барьцааны үнэлгээг тулган баталгаажуулна уу."
    )
    return f"Зээлдэгчийн эрсдэлийг ангилж тайлбарла: {base_input(data)}", response


def ratio_explanation(data: dict) -> tuple[str, str]:
    calc = metrics(data)
    response = (
        "Гол санхүүгийн харьцаанууд\n"
        f"- Ашиг = орлого - зардал = {money(calc['profit'])}.\n"
        f"- Ашгийн маржин = ашиг / орлого = {percent(calc['profit_margin'])}; үйл ажиллагааны ашигт ажиллагааг харуулна.\n"
        f"- Өр/орлого = {percent(calc['debt_to_revenue'])}; орлоготой харьцуулсан өрийн дарамт.\n"
        f"- Мөнгө/өр = {percent(calc['cash_to_debt'])}; ойрын төлбөр даах нөөц.\n"
        f"- Зардлын харьцаа = {percent(calc['expense_ratio'])}; зардлын сахилга батыг үнэлнэ. "
        "Та эдгээрийг дансны хуулга, татварын тайлантай тулгаж шалгана уу."
    )
    return f"Зээлдүүлэгчид хэрэгтэй санхүүгийн харьцааг тайлбарла: {base_input(data)}", response


def application_summary(data: dict) -> tuple[str, str]:
    calc = metrics(data)
    level = risk_level(data, calc)
    response = (
        "Зээлийн хүсэлтийн хураангуй\n"
        f"- Хүсэлт: {money(data['loan_amount'])}, {data['term_months']} сарын хугацаа.\n"
        f"- Бизнес: {data['sector']}; орлого {money(data['revenue'])}, зардал {money(data['expense'])}, ашиг {money(calc['profit'])}.\n"
        f"- Барьцаа: {data['collateral']}, үнэлгээ {money(data['collateral_value'])}, бүрхэлт {calc['collateral_coverage']:.2f}x.\n"
        f"- Эрсдэл: {level}; дутуу баримт: {data['missing_doc']}.\n"
        "Та хүсэлтийг эцсийн зөвшөөрөл гэж үзэлгүй, нэмэлт баталгаажуулалтын дараа шийдвэрлэнэ үү."
    )
    return f"Зээлийн хүсэлтийг товч хураангуйл: {base_input(data)}", response


def collateral_assessment(data: dict) -> tuple[str, str]:
    calc = metrics(data)
    level = "Бага" if calc["collateral_coverage"] >= 2.0 else "Дунд" if calc["collateral_coverage"] >= 1.2 else "Өндөр"
    response = (
        "Барьцааны үнэлгээ\n"
        f"- Барьцаа: {data['collateral']}; үнэлгээ {money(data['collateral_value'])}.\n"
        f"- Зээлийн дүн: {money(data['loan_amount'])}; барьцааны бүрхэлт {calc['collateral_coverage']:.2f}x.\n"
        f"- Барьцааны эрсдэл: {level}; хөрвөх чадвар, өмчлөл, даатгал, үнэлгээний огноог шалгана.\n"
        f"- Дутуу баримт: {data['missing_doc']}.\n"
        "Та барьцаа хангалттай байсан ч орлогын мөнгөн урсгалыг тусад нь баталгаажуулах шаардлагатай."
    )
    return f"Барьцааны хангалттай эсэхийг үнэл: {base_input(data)}", response


def repayment_capacity(data: dict) -> tuple[str, str]:
    calc = metrics(data)
    coverage = calc["profit"] / calc["monthly_repayment"] if calc["monthly_repayment"] else 0
    level = "Бага" if coverage >= 4 else "Дунд" if coverage >= 2 else "Өндөр"
    response = (
        "Төлбөрийн чадварын шинжилгээ\n"
        f"- Сарын ойролцоо төлөлт: {money(calc['monthly_repayment'])}.\n"
        f"- Ашиг {money(calc['profit'])}; ашиг/сарын төлөлт {coverage:.2f}x.\n"
        f"- Өр/орлого {percent(calc['debt_to_revenue'])}, мөнгө/өр {percent(calc['cash_to_debt'])}.\n"
        f"- Эрсдэлийн түвшин: {level}; улирлын хэлбэлзэл болон дансны бодит орлогыг шалгана.\n"
        f"- Дутуу баримт: {data['missing_doc']}. Эцсийн шийдвэр нэмэлт хяналтын дараа гарна."
    )
    return f"Төлбөрийн чадварыг тооцоотой үнэл: {base_input(data)}", response


def red_flags(data: dict) -> tuple[str, str]:
    calc = metrics(data)
    flags = []
    if calc["debt_to_revenue"] > 0.7:
        flags.append("өрийн ачаалал орлоготой харьцуулахад өндөр")
    if calc["cash_to_debt"] < 0.2:
        flags.append("мөнгөн нөөц өр төлбөрт хүрэлцэхгүй")
    if calc["expense_ratio"] > 0.72:
        flags.append("зардлын харьцаа өндөр")
    if calc["collateral_coverage"] < 1.3:
        flags.append("барьцааны бүрхэлт сул")
    if not flags:
        flags.append("томоохон улаан дохио бага боловч баримтын тулгалт шаардлагатай")
    response = (
        "Улаан дохионы шалгалт\n"
        f"- Илэрсэн эрсдэл: {', '.join(flags)}.\n"
        f"- Тооцоо: өр/орлого {percent(calc['debt_to_revenue'])}, мөнгө/өр {percent(calc['cash_to_debt'])}, "
        f"зардлын харьцаа {percent(calc['expense_ratio'])}.\n"
        f"- Дутуу баримт: {data['missing_doc']}.\n"
        "Та эдгээрийг тайлбарлах нэмэлт баримт авсны дараа шийдвэрийн санал боловсруулна уу."
    )
    return f"Зээлийн хүсэлтээс улаан дохио илрүүл: {base_input(data)}", response


def lender_recommendation(data: dict) -> tuple[str, str]:
    calc = metrics(data)
    level = risk_level(data, calc)
    response = (
        "Зээлдүүлэгчийн санал\n"
        f"- Эрсдэл: {level}; ашиг {money(calc['profit'])}, ашгийн маржин {percent(calc['profit_margin'])}, "
        f"өр/орлого {percent(calc['debt_to_revenue'])}.\n"
        f"- Нөхцөл: {money(data['loan_amount'])}-оос хэтрүүлэхгүй, {data['term_months']} сарын дотор, "
        "орлого баталгаажсаны дараа олгох боломжийг судална.\n"
        f"- Шаардлагатай баримт: {data['missing_doc']}.\n"
        f"- {recommendation(level)}"
    )
    return f"Зээлдүүлэгчийн практик шийдвэрийн санал бич: {base_input(data)}", response


def statement_summary(data: dict) -> tuple[str, str]:
    calc = metrics(data)
    level = risk_level(data, calc)
    response = (
        "Санхүүгийн тайлангийн хураангуй\n"
        f"- Орлого {money(data['revenue'])}, зардал {money(data['expense'])}, ашиг {money(calc['profit'])}.\n"
        f"- Ашгийн маржин {percent(calc['profit_margin'])}, зардлын харьцаа {percent(calc['expense_ratio'])}.\n"
        f"- Өр төлбөр {money(data['debt'])}, мөнгөн үлдэгдэл {money(data['cash'])}, мөнгө/өр {percent(calc['cash_to_debt'])}.\n"
        f"- Эрсдэлийн түвшин: {level}; {data['sector']} бизнесийн ашигт ажиллагаа болон өрийн дарамтыг хамтад нь үнэлэх шаардлагатай.\n"
        f"- Дутуу баримт: {data['missing_doc']}."
    )
    return f"Санхүүгийн тайланг зээлдүүлэгчид зориулж хураангуйл: {base_input(data)}", response


def cash_flow_decision(data: dict) -> tuple[str, str]:
    calc = metrics(data)
    net_after_debt = calc["profit"] - calc["monthly_repayment"]
    level = "Бага" if net_after_debt > data["loan_amount"] * 0.15 else "Дунд" if net_after_debt > 0 else "Өндөр"
    response = (
        "Мөнгөн урсгалд суурилсан шийдвэр\n"
        f"- Ашиг {money(calc['profit'])}; сарын төлөлт {money(calc['monthly_repayment'])}; "
        f"төлөлтийн дараах үлдэх дүн {money(net_after_debt)}.\n"
        f"- Өр/орлого {percent(calc['debt_to_revenue'])}; мөнгө/өр {percent(calc['cash_to_debt'])}.\n"
        f"- Эрсдэлийн түвшин: {level}; мөнгөн урсгал тасалдах эсэхийг дансны хуулгаар шалгана.\n"
        f"- Дутуу баримт: {data['missing_doc']}.\n"
        "Та эцсийн шийдвэрийг зөвхөн баталгаажуулсан мөнгөн урсгал, барьцаа, бодлогын шалгуурт үндэслэн гаргана уу."
    )
    return f"Мөнгөн урсгалд суурилсан зээлийн шийдвэр гарга: {base_input(data)}", response


BUILDERS = {
    "credit_memo": memo_body,
    "borrower_risk_classification": risk_classification,
    "financial_ratio_explanation": ratio_explanation,
    "loan_application_summary": application_summary,
    "collateral_assessment": collateral_assessment,
    "repayment_capacity_analysis": repayment_capacity,
    "red_flag_detection": red_flags,
    "lender_recommendation": lender_recommendation,
    "financial_statement_summary": statement_summary,
    "cash_flow_lending_decision": cash_flow_decision,
}


def make_record(index: int) -> dict:
    task = TASKS[index % len(TASKS)]
    data = scenario(index)
    user, assistant = BUILDERS[task](data)
    return {
        "id": f"lendex-v2-{index + 1:05d}",
        "messages": [
            {
                "role": "system",
                "content": (
                    "Та Lendex болон Datagate-д зориулсан монгол хэлтэй зээлийн шинжээч. "
                    "Дотоод бодлоо бүү харуул. Богино, бүтэцтэй, тооцоотой, мэргэжлийн хариул."
                ),
            },
            {"role": "user", "content": user},
            {"role": "assistant", "content": assistant},
        ],
        "metadata": {
            "domain": task,
            "source": "synthetic_lendex_credit_analyst_v2",
            "license_status": "synthetic",
            "allowed_usage": "training_allowed",
            "contains_pii": False,
            "numeric_example": True,
            "metrics_expected": True,
        },
    }


def write_jsonl(path: Path, records: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="Build Lendex/DataGate Mongolian credit analyst SFT v2 dataset.")
    parser.add_argument("--count", type=int, default=2000)
    parser.add_argument("--train-output", type=Path, default=TRAIN_OUTPUT)
    parser.add_argument("--val-output", type=Path, default=VAL_OUTPUT)
    args = parser.parse_args()

    if args.count < 2000:
        raise SystemExit("--count must be at least 2000 for v2 dataset quality.")
    records = [make_record(index) for index in range(args.count)]
    split = int(args.count * 0.9)
    train_records = records[:split]
    val_records = records[split:]
    write_jsonl(args.train_output, train_records)
    write_jsonl(args.val_output, val_records)
    print(json.dumps({
        "total": len(records),
        "train": len(train_records),
        "validation": len(val_records),
        "train_output": str(args.train_output),
        "val_output": str(args.val_output),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
