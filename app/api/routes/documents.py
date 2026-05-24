from fastapi import APIRouter, HTTPException, Query, status

from app.api.deps import ApiKey, Auditor, ClientIp, DocService, RequestId
from app.models.audit import AuditAction, AuditOutcome
from app.models.document import Document, DocumentCreate, DocumentList, DocumentWithContent
from app.services.document_service import DocumentNotFoundError

router = APIRouter(prefix="/documents", tags=["Documents"])


@router.post("", response_model=Document, status_code=status.HTTP_201_CREATED)
async def create_document(
    payload: DocumentCreate,
    api_key: ApiKey,
    request_id: RequestId,
    client_ip: ClientIp,
    doc_service: DocService,
    auditor: Auditor,
) -> Document:
    doc = doc_service.create(payload)
    auditor.record(
        action=AuditAction.DOCUMENT_CREATE,
        request_id=request_id,
        ip_address=client_ip,
        api_key=api_key,
        outcome=AuditOutcome.SUCCESS,
        resource_id=doc.id,
    )
    return doc


@router.get("", response_model=DocumentList, tags=["Documents"])
async def list_documents(
    api_key: ApiKey,
    request_id: RequestId,
    client_ip: ClientIp,
    doc_service: DocService,
    auditor: Auditor,
    patient_id: str | None = Query(None, description="Filter by patient ID"),
) -> DocumentList:
    result = doc_service.list_documents(patient_id=patient_id)
    auditor.record(
        action=AuditAction.DOCUMENT_LIST,
        request_id=request_id,
        ip_address=client_ip,
        api_key=api_key,
        outcome=AuditOutcome.SUCCESS,
    )
    return result


@router.get("/{document_id}", response_model=Document)
async def get_document(
    document_id: str,
    api_key: ApiKey,
    request_id: RequestId,
    client_ip: ClientIp,
    doc_service: DocService,
    auditor: Auditor,
    include_content: bool = Query(False, description="Include decrypted document content"),
) -> Document | DocumentWithContent:
    try:
        doc = doc_service.get(document_id, include_content=include_content)
    except DocumentNotFoundError:
        auditor.record(
            action=AuditAction.DOCUMENT_READ,
            request_id=request_id,
            ip_address=client_ip,
            api_key=api_key,
            outcome=AuditOutcome.FAILURE,
            resource_id=document_id,
            detail="not_found",
        )
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    auditor.record(
        action=AuditAction.DOCUMENT_READ,
        request_id=request_id,
        ip_address=client_ip,
        api_key=api_key,
        outcome=AuditOutcome.SUCCESS,
        resource_id=document_id,
    )
    return doc
