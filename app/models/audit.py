from datetime import datetime
from enum import Enum

from pydantic import BaseModel


class AuditAction(str, Enum):
    DOCUMENT_CREATE = "document.create"
    DOCUMENT_READ = "document.read"
    DOCUMENT_LIST = "document.list"
    ANALYSIS_CREATE = "analysis.create"
    ANALYSIS_READ = "analysis.read"
    AGENT_QUERY = "agent.query"


class AuditOutcome(str, Enum):
    SUCCESS = "success"
    FAILURE = "failure"
    DENIED = "denied"


class AuditLog(BaseModel):
    id: str
    timestamp: datetime
    action: AuditAction
    resource_id: str | None
    api_key_prefix: str  # first 8 chars only — never log full key
    request_id: str
    ip_address: str
    outcome: AuditOutcome
    detail: str | None = None


class AuditLogList(BaseModel):
    logs: list[AuditLog]
    total: int
