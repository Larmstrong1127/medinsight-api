import json
import uuid
from datetime import UTC, datetime
from pathlib import Path

import boto3
from botocore.exceptions import ClientError

from app.config import get_settings
from app.core.logging import get_logger
from app.models.audit import AuditAction, AuditLog, AuditLogList, AuditOutcome

logger = get_logger(__name__)


class AuditService:
    def __init__(self) -> None:
        self.settings = get_settings()
        self._local_path = Path(self.settings.local_storage_path) / "audit_logs.jsonl"

    def _use_aws(self) -> bool:
        return self.settings.storage_backend == "aws"

    def record(
        self,
        action: AuditAction,
        request_id: str,
        ip_address: str,
        api_key: str,
        outcome: AuditOutcome,
        resource_id: str | None = None,
        detail: str | None = None,
    ) -> AuditLog:
        log = AuditLog(
            id=str(uuid.uuid4()),
            timestamp=datetime.now(tz=UTC),
            action=action,
            resource_id=resource_id,
            api_key_prefix=api_key[:8] if len(api_key) >= 8 else api_key,
            request_id=request_id,
            ip_address=ip_address,
            outcome=outcome,
            detail=detail,
        )

        if self._use_aws():
            self._write_dynamodb(log)
        else:
            self._write_local(log)

        logger.info(
            "audit",
            action=log.action,
            resource_id=log.resource_id,
            outcome=log.outcome,
            request_id=request_id,
        )
        return log

    def _write_local(self, log: AuditLog) -> None:
        self._local_path.parent.mkdir(parents=True, exist_ok=True)
        with self._local_path.open("a") as f:
            f.write(log.model_dump_json() + "\n")

    def _write_dynamodb(self, log: AuditLog) -> None:
        client = boto3.resource("dynamodb", region_name=self.settings.aws_region)
        table = client.Table(self.settings.audit_table)
        try:
            table.put_item(Item=json.loads(log.model_dump_json()))
        except ClientError as e:
            logger.error("audit_dynamodb_write_failed", error=str(e))

    def list_logs(self, limit: int = 100, offset: int = 0) -> AuditLogList:
        if self._use_aws():
            return self._list_dynamodb(limit, offset)
        return self._list_local(limit, offset)

    def _list_local(self, limit: int, offset: int) -> AuditLogList:
        if not self._local_path.exists():
            return AuditLogList(logs=[], total=0)
        lines = self._local_path.read_text().strip().splitlines()
        total = len(lines)
        page = lines[offset : offset + limit]
        logs = [AuditLog.model_validate_json(line) for line in page]
        return AuditLogList(logs=logs, total=total)

    def _list_dynamodb(self, limit: int, offset: int) -> AuditLogList:
        client = boto3.resource("dynamodb", region_name=self.settings.aws_region)
        table = client.Table(self.settings.audit_table)
        response = table.scan(Limit=limit)
        items = response.get("Items", [])
        logs = [AuditLog.model_validate(item) for item in items]
        return AuditLogList(logs=logs, total=len(logs))
