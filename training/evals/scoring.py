def heuristic_score(expected: str) -> float:
    if not expected:
        return 0.5
    if len(expected.strip()) < 10:
        return 0.65
    return 0.8
