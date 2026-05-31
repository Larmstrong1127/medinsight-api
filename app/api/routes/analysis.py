from fastapi import APIRouter, HTTPException, status

from app.agents.clinical_agent import AgentQuery, AgentResponse
from app.api.deps import (
    Agent,
    AnalysisService,
    ApiKey,
    Auditor,
    ClientIp,
    RequestId,
)
from app.models.analysis import Analysis, AnalysisRequest
from app.models.audit import AuditAction, AuditOutcome
from app.services.document_service import DocumentNotFoundError

router = APIRouter(tags=["Analysis"])


@router.post("/analysis", response_model=Analysis, status_code=status.HTTP_201_CREATED)
async def analyze_document(
    request: AnalysisRequest,
    api_key: ApiKey,
    request_id: RequestId,
    client_ip: ClientIp,
    llm_service: AnalysisService,
    auditor: Auditor,
) -> Analysis:
    try:
        analysis = await llm_service.analyze(request)
    except DocumentNotFoundError:
        auditor.record(
            action=AuditAction.ANALYSIS_CREATE,
            request_id=request_id,
            ip_address=client_ip,
            api_key=api_key,
            outcome=AuditOutcome.FAILURE,
            resource_id=request.document_id,
            detail="document_not_found",
        )
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found") from None

    auditor.record(
        action=AuditAction.ANALYSIS_CREATE,
        request_id=request_id,
        ip_address=client_ip,
        api_key=api_key,
        outcome=AuditOutcome.SUCCESS,
        resource_id=analysis.id,
    )
    return analysis


@router.post("/agent/query", response_model=AgentResponse)
async def agent_query(
    query: AgentQuery,
    api_key: ApiKey,
    request_id: RequestId,
    client_ip: ClientIp,
    agent: Agent,
    auditor: Auditor,
) -> AgentResponse:
    response = await agent.query(query)
    auditor.record(
        action=AuditAction.AGENT_QUERY,
        request_id=request_id,
        ip_address=client_ip,
        api_key=api_key,
        outcome=AuditOutcome.SUCCESS,
    )
    return response
