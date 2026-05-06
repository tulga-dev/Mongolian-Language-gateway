from fastapi import APIRouter, Request

from app.schemas import EvaluationRequest, EvaluationResponse, EvaluationScore

router = APIRouter(prefix="/v1", tags=["evaluation"])


@router.post("/evaluate", response_model=EvaluationResponse)
async def evaluate(payload: EvaluationRequest, request: Request) -> EvaluationResponse:
    settings = request.app.state.settings
    judge_model = payload.judge_model or settings.teacher_model
    scores: list[EvaluationScore] = []
    for item in payload.items:
        has_expected = bool(item.expected and item.expected.strip())
        score = 0.8 if has_expected else 0.5
        notes = "Placeholder heuristic score. Use teacher/evaluator model for production grading."
        scores.append(EvaluationScore(item_id=item.id, score=score, notes=notes))
    average = round(sum(score.score for score in scores) / len(scores), 3)
    return EvaluationResponse(
        benchmark_name=payload.benchmark_name,
        average_score=average,
        scores=scores,
        judge_model=judge_model,
    )
