from app.schemas import ComplianceIssue


RISK_PATTERNS = [
    {
        "category": "guaranteed approval",
        "phrases": ["guaranteed approval", "баталгаатай зөвшөөрнө", "заавал батална"],
        "severity": "high",
        "alternative": "Таны хүсэлтийг банкны эцсийн хяналт, шаардлагын дагуу шийдвэрлэнэ.",
    },
    {
        "category": "final approval promise",
        "phrases": ["final approval is confirmed", "эцсийн зөвшөөрөл гарсан", "зээл тань батлагдсан"],
        "severity": "high",
        "alternative": "Урьдчилсан мэдээлэлд үндэслэн боломжийг шалгаж байгаа бөгөөд эцсийн шийдвэр хяналтын дараа гарна.",
    },
    {
        "category": "misleading interest/fee wording",
        "phrases": ["no fees", "hidden fee байхгүй", "хамгийн бага хүүтэй"],
        "severity": "medium",
        "alternative": "Хүү, шимтгэлийн нөхцөл нь бүтээгдэхүүн, шалгуур болон гэрээний нөхцлөөс хамаарна.",
    },
    {
        "category": "missing final review disclaimer",
        "phrases": ["pre-approved", "урьдчилан зөвшөөрөгдсөн"],
        "severity": "medium",
        "alternative": "Энэ нь урьдчилсан үнэлгээ бөгөөд эцсийн шийдвэрийг нэмэлт хяналтын дараа гаргана.",
    },
    {
        "category": "unsafe rejection explanations",
        "phrases": ["blacklisted", "та муу зээлдэгч", "you are a bad borrower"],
        "severity": "high",
        "alternative": "Одоогийн мэдээллээр хүсэлтийг үргэлжлүүлэх боломжгүй байна. Дэлгэрэнгүй шалтгааныг албан ёсны сувгаар тайлбарлана.",
    },
]


def check_lending_compliance(text: str) -> tuple[list[ComplianceIssue], str | None]:
    lowered = text.lower()
    issues: list[ComplianceIssue] = []
    safer_text = text
    for pattern in RISK_PATTERNS:
        for phrase in pattern["phrases"]:
            if phrase.lower() in lowered:
                issue = ComplianceIssue(
                    category=pattern["category"],
                    phrase=phrase,
                    severity=pattern["severity"],
                    explanation=f"Detected risky lending wording: {pattern['category']}.",
                    safer_mongolian_alternative=pattern["alternative"],
                )
                issues.append(issue)
                safer_text = safer_text.replace(phrase, pattern["alternative"])
    if not issues:
        return [], None
    return issues, safer_text


def safer_alternatives(issues: list[ComplianceIssue]) -> list[str]:
    return [issue.safer_mongolian_alternative for issue in issues]
