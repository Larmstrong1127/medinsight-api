from fastapi import APIRouter, Query

from app.api.deps import ApiKey, Auditor
from app.models.audit import AuditLogList

router = APIRouter(prefix="/audit", tags=["Audit"])


@router.get("/logs", response_model=AuditLogList)
async def list_audit_logs(
    api_key: ApiKey,
    auditor: Auditor,
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
) -> AuditLogList:
    return auditor.list_logs(limit=limit, offset=offset)
