def average_score(scores: list[dict]) -> float:
    if not scores:
        return 0.0
    return round(sum(item["score"] for item in scores) / len(scores), 3)
