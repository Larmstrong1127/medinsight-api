from openai import AsyncOpenAI

from app.config import get_settings
from app.core.logging import get_logger
from app.models.analysis import (
    Analysis,
    AnalysisRequest,
    AnalysisResult,
    AnalysisType,
    Diagnosis,
    Medication,
    RiskFactor,
)
from app.services.document_service import DocumentService

import json
import uuid
from datetime import datetime, timezone

logger = get_logger(__name__)

_SYSTEM_PROMPT = """You are a clinical NLP assistant. Analyze the provided clinical note and extract
structured information. Always respond with valid JSON matching the requested schema exactly.
Never hallucinate patient information not present in the note. Mark confidence as 0.0 when uncertain."""

_PROMPTS: dict[AnalysisType, str] = {
    AnalysisType.SUMMARIZE: """Summarize this clinical note in 2-3 sentences.
Return JSON: {"summary": "..."}""",

    AnalysisType.EXTRACT_DIAGNOSES: """Extract all diagnoses and conditions mentioned.
Return JSON: {"diagnoses": [{"code": "ICD-10 if determinable or null", "description": "...", "confidence": 0.0-1.0}]}""",

    AnalysisType.EXTRACT_MEDICATIONS: """Extract all medications mentioned.
Return JSON: {"medications": [{"name": "...", "dosage": "or null", "frequency": "or null", "route": "or null"}]}""",

    AnalysisType.RISK_ASSESSMENT: """Identify clinical risk factors.
Return JSON: {"risk_factors": [{"factor": "...", "severity": "low|medium|high", "rationale": "..."}]}""",

    AnalysisType.FULL_ANALYSIS: """Perform full analysis: summary, diagnoses, medications, and risk factors.
Return JSON with all fields: {"summary": "...", "diagnoses": [...], "medications": [...], "risk_factors": [...]}""",
}


class LLMService:
    def __init__(self) -> None:
        self.settings = get_settings()
        self._client = AsyncOpenAI(api_key=self.settings.openai_api_key)
        self._doc_service = DocumentService()

    async def analyze(self, request: AnalysisRequest) -> Analysis:
        doc = self._doc_service.get(request.document_id, include_content=True)
        content = doc.content  # type: ignore[union-attr]

        user_message = f"Clinical Note:\n{content}"
        if request.context:
            user_message += f"\n\nAdditional context: {request.context}"

        prompt = _PROMPTS[request.analysis_type]

        logger.info(
            "llm_analysis_start",
            doc_id=request.document_id,
            analysis_type=request.analysis_type,
            model=self.settings.openai_model,
        )

        response = await self._client.chat.completions.create(
            model=self.settings.openai_model,
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": f"{prompt}\n\n{user_message}"},
            ],
            response_format={"type": "json_object"},
            temperature=0.1,
        )

        raw = json.loads(response.choices[0].message.content or "{}")
        result = self._parse_result(request.analysis_type, raw)

        logger.info(
            "llm_analysis_complete",
            doc_id=request.document_id,
            analysis_type=request.analysis_type,
            tokens_used=response.usage.total_tokens if response.usage else None,
        )

        return Analysis(
            id=str(uuid.uuid4()),
            document_id=request.document_id,
            analysis_type=request.analysis_type,
            result=result,
            model_used=self.settings.openai_model,
            created_at=datetime.now(tz=timezone.utc),
        )

    def _parse_result(self, analysis_type: AnalysisType, raw: dict) -> AnalysisResult:
        return AnalysisResult(
            summary=raw.get("summary"),
            diagnoses=[
                Diagnosis(**d) if isinstance(d, dict) else Diagnosis(description=d, confidence=0.8)
                for d in raw.get("diagnoses", [])
            ],
            medications=[
                Medication(**m) if isinstance(m, dict) else Medication(name=m)
                for m in raw.get("medications", [])
            ],
            risk_factors=[
                RiskFactor(**r) if isinstance(r, dict) else RiskFactor(factor=r, severity="medium", rationale="")
                for r in raw.get("risk_factors", [])
            ],
            raw=raw,
        )
