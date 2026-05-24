import uuid
from typing import Annotated

from fastapi import Depends, Request
from fastapi.security import APIKeyHeader

from app.core.security import verify_api_key
from app.services.audit_service import AuditService
from app.services.document_service import DocumentService
from app.services.llm_service import LLMService
from app.agents.clinical_agent import ClinicalAgent

api_key_scheme = APIKeyHeader(name="X-API-Key")


def get_request_id(request: Request) -> str:
    return request.headers.get("X-Request-ID", str(uuid.uuid4()))


def get_client_ip(request: Request) -> str:
    forwarded = request.headers.get("X-Forwarded-For")
    return forwarded.split(",")[0].strip() if forwarded else (request.client.host if request.client else "unknown")


def get_document_service() -> DocumentService:
    return DocumentService()


def get_llm_service() -> LLMService:
    return LLMService()


def get_audit_service() -> AuditService:
    return AuditService()


def get_clinical_agent() -> ClinicalAgent:
    return ClinicalAgent()


ApiKey = Annotated[str, Depends(verify_api_key)]
RequestId = Annotated[str, Depends(get_request_id)]
ClientIp = Annotated[str, Depends(get_client_ip)]
DocService = Annotated[DocumentService, Depends(get_document_service)]
AnalysisService = Annotated[LLMService, Depends(get_llm_service)]
Auditor = Annotated[AuditService, Depends(get_audit_service)]
Agent = Annotated[ClinicalAgent, Depends(get_clinical_agent)]
