import hashlib
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

import boto3
from botocore.exceptions import ClientError

from app.config import get_settings
from app.core.logging import get_logger
from app.core.security import decrypt_content, encrypt_content
from app.models.document import Document, DocumentCreate, DocumentList, DocumentWithContent

logger = get_logger(__name__)


class DocumentNotFoundError(Exception):
    pass


class DocumentService:
    def __init__(self) -> None:
        self.settings = get_settings()
        self._local_path = Path(self.settings.local_storage_path) / "documents"

    def _use_aws(self) -> bool:
        return self.settings.storage_backend == "aws"

    def create(self, payload: DocumentCreate) -> Document:
        doc_id = str(uuid.uuid4())
        checksum = hashlib.sha256(payload.content.encode()).hexdigest()
        encrypted = encrypt_content(payload.content)
        now = datetime.now(tz=timezone.utc)

        record = {
            "id": doc_id,
            "patient_id": payload.patient_id,
            "document_type": payload.document_type.value,
            "metadata": payload.metadata,
            "checksum": checksum,
            "created_at": now.isoformat(),
            "_encrypted_content": encrypted,
        }

        if self._use_aws():
            self._save_s3(doc_id, record)
        else:
            self._save_local(doc_id, record)

        logger.info("document_created", doc_id=doc_id, patient_id=payload.patient_id)
        return Document(
            id=doc_id,
            patient_id=payload.patient_id,
            document_type=payload.document_type,
            metadata=payload.metadata,
            checksum=checksum,
            created_at=now,
        )

    def get(self, doc_id: str, include_content: bool = False) -> Document | DocumentWithContent:
        record = self._load(doc_id)
        doc = Document(
            id=record["id"],
            patient_id=record["patient_id"],
            document_type=record["document_type"],
            metadata=record["metadata"],
            checksum=record["checksum"],
            created_at=datetime.fromisoformat(record["created_at"]),
        )
        if include_content:
            return DocumentWithContent(
                **doc.model_dump(),
                content=decrypt_content(record["_encrypted_content"]),
            )
        return doc

    def list_documents(self, patient_id: str | None = None) -> DocumentList:
        if self._use_aws():
            records = self._list_s3(patient_id)
        else:
            records = self._list_local(patient_id)

        docs = [
            Document(
                id=r["id"],
                patient_id=r["patient_id"],
                document_type=r["document_type"],
                metadata=r["metadata"],
                checksum=r["checksum"],
                created_at=datetime.fromisoformat(r["created_at"]),
            )
            for r in records
        ]
        return DocumentList(documents=docs, total=len(docs))

    # ── Local storage (dev) ──────────────────────────────────────────────────

    def _save_local(self, doc_id: str, record: dict) -> None:
        self._local_path.mkdir(parents=True, exist_ok=True)
        path = self._local_path / f"{doc_id}.json"
        path.write_text(json.dumps(record, default=str))

    def _load(self, doc_id: str) -> dict:
        if self._use_aws():
            return self._load_s3(doc_id)
        path = self._local_path / f"{doc_id}.json"
        if not path.exists():
            raise DocumentNotFoundError(doc_id)
        return json.loads(path.read_text())

    def _list_local(self, patient_id: str | None) -> list[dict]:
        if not self._local_path.exists():
            return []
        records = [json.loads(p.read_text()) for p in self._local_path.glob("*.json")]
        if patient_id:
            records = [r for r in records if r["patient_id"] == patient_id]
        return records

    # ── AWS S3 storage (production) ──────────────────────────────────────────

    def _save_s3(self, doc_id: str, record: dict) -> None:
        client = boto3.client("s3", region_name=self.settings.aws_region)
        try:
            client.put_object(
                Bucket=self.settings.s3_bucket,
                Key=f"documents/{doc_id}.json",
                Body=json.dumps(record, default=str),
                ContentType="application/json",
                ServerSideEncryption="aws:kms",
            )
        except ClientError as e:
            logger.error("s3_write_failed", error=str(e))
            raise

    def _load_s3(self, doc_id: str) -> dict:
        client = boto3.client("s3", region_name=self.settings.aws_region)
        try:
            resp = client.get_object(
                Bucket=self.settings.s3_bucket,
                Key=f"documents/{doc_id}.json",
            )
            return json.loads(resp["Body"].read())
        except ClientError as e:
            if e.response["Error"]["Code"] == "NoSuchKey":
                raise DocumentNotFoundError(doc_id) from e
            raise

    def _list_s3(self, patient_id: str | None) -> list[dict]:
        client = boto3.client("s3", region_name=self.settings.aws_region)
        paginator = client.get_paginator("list_objects_v2")
        records = []
        for page in paginator.paginate(Bucket=self.settings.s3_bucket, Prefix="documents/"):
            for obj in page.get("Contents", []):
                record = self._load_s3(obj["Key"].split("/")[-1].replace(".json", ""))
                if patient_id is None or record["patient_id"] == patient_id:
                    records.append(record)
        return records
