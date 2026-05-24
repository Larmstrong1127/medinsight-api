from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class DocumentType(str, Enum):
    ADMISSION_NOTE = "admission_note"
    DISCHARGE_SUMMARY = "discharge_summary"
    PROGRESS_NOTE = "progress_note"
    RADIOLOGY_REPORT = "radiology_report"
    LAB_REPORT = "lab_report"
    OPERATIVE_NOTE = "operative_note"


class DocumentCreate(BaseModel):
    content: str = Field(..., min_length=10, description="Raw clinical note text")
    patient_id: str = Field(..., description="De-identified patient identifier")
    document_type: DocumentType
    metadata: dict = Field(default_factory=dict)


class Document(BaseModel):
    id: str
    patient_id: str
    document_type: DocumentType
    metadata: dict
    checksum: str
    created_at: datetime
    # content is omitted from responses — must be explicitly requested


class DocumentWithContent(Document):
    content: str


class DocumentList(BaseModel):
    documents: list[Document]
    total: int
