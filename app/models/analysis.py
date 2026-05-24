from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class AnalysisType(str, Enum):
    SUMMARIZE = "summarize"
    EXTRACT_DIAGNOSES = "extract_diagnoses"
    EXTRACT_MEDICATIONS = "extract_medications"
    RISK_ASSESSMENT = "risk_assessment"
    FULL_ANALYSIS = "full_analysis"


class AnalysisRequest(BaseModel):
    document_id: str
    analysis_type: AnalysisType
    context: str | None = Field(None, description="Optional clinical context or question")


class Diagnosis(BaseModel):
    code: str | None = None
    description: str
    confidence: float = Field(ge=0.0, le=1.0)


class Medication(BaseModel):
    name: str
    dosage: str | None = None
    frequency: str | None = None
    route: str | None = None


class RiskFactor(BaseModel):
    factor: str
    severity: str  # low | medium | high
    rationale: str


class AnalysisResult(BaseModel):
    summary: str | None = None
    diagnoses: list[Diagnosis] = []
    medications: list[Medication] = []
    risk_factors: list[RiskFactor] = []
    raw: dict[str, Any] = Field(default_factory=dict)


class Analysis(BaseModel):
    id: str
    document_id: str
    analysis_type: AnalysisType
    result: AnalysisResult
    model_used: str
    created_at: datetime
