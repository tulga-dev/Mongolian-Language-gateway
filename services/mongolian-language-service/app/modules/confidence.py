def heuristic_confidence(text: str, warnings: list[str] | None = None) -> float:
    warnings = warnings or []
    score = 0.88
    if len(text.strip()) < 20:
        score -= 0.1
    if warnings:
        score -= min(0.25, 0.05 * len(warnings))
    return max(0.2, min(0.98, round(score, 2)))
