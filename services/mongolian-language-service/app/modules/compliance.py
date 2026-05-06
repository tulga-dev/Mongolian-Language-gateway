from app.schemas import ComplianceIssue


RISK_PATTERNS = [
    {
        "category": "guaranteed approval",
        "phrases": [
            "guaranteed approval",
            "\u0431\u0430\u0442\u0430\u043b\u0433\u0430\u0430\u0442\u0430\u0439 \u0437\u04e9\u0432\u0448\u04e9\u04e9\u0440\u043d\u04e9",
            "\u0437\u0430\u0430\u0432\u0430\u043b \u0431\u0430\u0442\u0430\u043b\u043d\u0430",
        ],
        "severity": "high",
        "alternative": "\u0422\u0430\u043d\u044b \u0445\u04af\u0441\u044d\u043b\u0442\u0438\u0439\u0433 \u0431\u0430\u043d\u043a\u043d\u044b \u044d\u0446\u0441\u0438\u0439\u043d \u0445\u044f\u043d\u0430\u043b\u0442, \u0448\u0430\u0430\u0440\u0434\u043b\u0430\u0433\u044b\u043d \u0434\u0430\u0433\u0443\u0443 \u0448\u0438\u0439\u0434\u0432\u044d\u0440\u043b\u044d\u043d\u044d.",
    },
    {
        "category": "final approval promise",
        "phrases": [
            "final approval is confirmed",
            "\u044d\u0446\u0441\u0438\u0439\u043d \u0437\u04e9\u0432\u0448\u04e9\u04e9\u0440\u04e9\u043b \u0433\u0430\u0440\u0441\u0430\u043d",
            "\u0437\u044d\u044d\u043b \u0442\u0430\u043d\u044c \u0431\u0430\u0442\u043b\u0430\u0433\u0434\u0441\u0430\u043d",
        ],
        "severity": "high",
        "alternative": "\u0423\u0440\u044c\u0434\u0447\u0438\u043b\u0441\u0430\u043d \u043c\u044d\u0434\u044d\u044d\u043b\u044d\u043b\u0434 \u04af\u043d\u0434\u044d\u0441\u043b\u044d\u043d \u0431\u043e\u043b\u043e\u043c\u0436\u0438\u0439\u0433 \u0448\u0430\u043b\u0433\u0430\u0436 \u0431\u0430\u0439\u0433\u0430\u0430 \u0431\u04e9\u0433\u04e9\u04e9\u0434 \u044d\u0446\u0441\u0438\u0439\u043d \u0448\u0438\u0439\u0434\u0432\u044d\u0440 \u0445\u044f\u043d\u0430\u043b\u0442\u044b\u043d \u0434\u0430\u0440\u0430\u0430 \u0433\u0430\u0440\u043d\u0430.",
    },
    {
        "category": "misleading interest/fee wording",
        "phrases": [
            "no fees",
            "no hidden fees",
            "0% interest",
            "hidden fee \u0431\u0430\u0439\u0445\u0433\u04af\u0439",
            "\u0445\u04af\u04af \u0448\u0438\u043c\u0442\u0433\u044d\u043b\u0433\u04af\u0439",
            "\u0445\u0430\u043c\u0433\u0438\u0439\u043d \u0431\u0430\u0433\u0430 \u0445\u04af\u04af\u0442\u044d\u0439",
        ],
        "severity": "medium",
        "alternative": "\u0425\u04af\u04af, \u0448\u0438\u043c\u0442\u0433\u044d\u043b\u0438\u0439\u043d \u043d\u04e9\u0445\u0446\u04e9\u043b \u043d\u044c \u0431\u04af\u0442\u044d\u044d\u0433\u0434\u044d\u0445\u04af\u04af\u043d, \u0448\u0430\u043b\u0433\u0443\u0443\u0440 \u0431\u043e\u043b\u043e\u043d \u0433\u044d\u0440\u044d\u044d\u043d\u0438\u0439 \u043d\u04e9\u0445\u0446\u043b\u04e9\u04e9\u0441 \u0445\u0430\u043c\u0430\u0430\u0440\u043d\u0430.",
    },
    {
        "category": "missing final review disclaimer",
        "phrases": [
            "pre-approved",
            "\u0443\u0440\u044c\u0434\u0447\u0438\u043b\u0430\u043d \u0437\u04e9\u0432\u0448\u04e9\u04e9\u0440\u04e9\u0433\u0434\u0441\u04e9\u043d",
        ],
        "severity": "medium",
        "alternative": "\u042d\u043d\u044d \u043d\u044c \u0443\u0440\u044c\u0434\u0447\u0438\u043b\u0441\u0430\u043d \u04af\u043d\u044d\u043b\u0433\u044d\u044d \u0431\u04e9\u0433\u04e9\u04e9\u0434 \u044d\u0446\u0441\u0438\u0439\u043d \u0448\u0438\u0439\u0434\u0432\u044d\u0440\u0438\u0439\u0433 \u043d\u044d\u043c\u044d\u043b\u0442 \u0445\u044f\u043d\u0430\u043b\u0442\u044b\u043d \u0434\u0430\u0440\u0430\u0430 \u0433\u0430\u0440\u0433\u0430\u043d\u0430.",
    },
    {
        "category": "unsafe rejection explanations",
        "phrases": [
            "blacklisted",
            "\u0442\u0430 \u043c\u0443\u0443 \u0437\u044d\u044d\u043b\u0434\u044d\u0433\u0447",
            "you are a bad borrower",
        ],
        "severity": "high",
        "alternative": "\u041e\u0434\u043e\u043e\u0433\u0438\u0439\u043d \u043c\u044d\u0434\u044d\u044d\u043b\u043b\u044d\u044d\u0440 \u0445\u04af\u0441\u044d\u043b\u0442\u0438\u0439\u0433 \u04af\u0440\u0433\u044d\u043b\u0436\u043b\u04af\u04af\u043b\u044d\u0445 \u0431\u043e\u043b\u043e\u043c\u0436\u0433\u04af\u0439 \u0431\u0430\u0439\u043d\u0430. \u0414\u044d\u043b\u0433\u044d\u0440\u044d\u043d\u0433\u04af\u0439 \u0448\u0430\u043b\u0442\u0433\u0430\u0430\u043d\u044b\u0433 \u0430\u043b\u0431\u0430\u043d \u0451\u0441\u043d\u044b \u0441\u0443\u0432\u0433\u0430\u0430\u0440 \u0442\u0430\u0439\u043b\u0431\u0430\u0440\u043b\u0430\u043d\u0430.",
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
