from fastapi import APIRouter

from app.modules.compliance import check_lending_compliance
from app.schemas import ComplianceCheckRequest, ComplianceCheckResponse

router = APIRouter(prefix="/v1", tags=["compliance"])


@router.post("/compliance-check", response_model=ComplianceCheckResponse)
async def compliance_check(payload: ComplianceCheckRequest) -> ComplianceCheckResponse:
    issues, safer_text = check_lending_compliance(payload.text)
    return ComplianceCheckResponse(is_safe=not issues, issues=issues, safer_text=safer_text)
