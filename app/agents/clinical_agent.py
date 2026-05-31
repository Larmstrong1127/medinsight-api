from langchain_core.messages import HumanMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from pydantic import BaseModel

from app.config import get_settings
from app.core.logging import get_logger
from app.models.analysis import AnalysisRequest, AnalysisType
from app.services.document_service import DocumentService
from app.services.llm_service import LLMService

logger = get_logger(__name__)


class AgentQuery(BaseModel):
    query: str
    patient_id: str | None = None


class AgentResponse(BaseModel):
    answer: str
    sources: list[str] = []


def _make_tools(doc_service: DocumentService, llm_service: LLMService):
    @tool
    def list_patient_documents(patient_id: str) -> str:
        """List all documents for a given patient ID."""
        result = doc_service.list_documents(patient_id=patient_id)
        if not result.documents:
            return f"No documents found for patient {patient_id}."
        lines = [f"- [{d.id}] {d.document_type} ({d.created_at.date()})" for d in result.documents]
        return f"Found {result.total} documents:\n" + "\n".join(lines)

    @tool
    async def get_document_summary(document_id: str) -> str:
        """Retrieve and summarize a specific clinical document by its ID."""
        request = AnalysisRequest(
            document_id=document_id,
            analysis_type=AnalysisType.SUMMARIZE,
        )
        analysis = await llm_service.analyze(request)
        return analysis.result.summary or "No summary available."

    @tool
    async def extract_diagnoses_from_document(document_id: str) -> str:
        """Extract diagnoses from a specific clinical document."""
        request = AnalysisRequest(
            document_id=document_id,
            analysis_type=AnalysisType.EXTRACT_DIAGNOSES,
        )
        analysis = await llm_service.analyze(request)
        if not analysis.result.diagnoses:
            return "No diagnoses extracted."
        return "\n".join(
            f"- {d.description} (confidence: {d.confidence:.0%})"
            for d in analysis.result.diagnoses
        )

    @tool
    async def assess_patient_risk(document_id: str) -> str:
        """Perform a risk assessment on a clinical document."""
        request = AnalysisRequest(
            document_id=document_id,
            analysis_type=AnalysisType.RISK_ASSESSMENT,
        )
        analysis = await llm_service.analyze(request)
        if not analysis.result.risk_factors:
            return "No risk factors identified."
        return "\n".join(
            f"- [{r.severity.upper()}] {r.factor}: {r.rationale}"
            for r in analysis.result.risk_factors
        )

    return [list_patient_documents, get_document_summary, extract_diagnoses_from_document, assess_patient_risk]


_SYSTEM_PROMPT = """You are a clinical intelligence assistant with access to a secure document store.
You can search for patient documents, summarize them, extract diagnoses, and assess risks.
Always be precise. Never speculate beyond what the documents contain.
When referencing a document, cite its ID.
If a patient_id is provided in the query, scope your searches to that patient."""


class ClinicalAgent:
    def __init__(self) -> None:
        settings = get_settings()
        self._doc_service = DocumentService()
        self._llm_service = LLMService()
        self._llm = ChatOpenAI(
            api_key=settings.openai_api_key,
            model=settings.openai_model,
            temperature=0,
        )
        tools = _make_tools(self._doc_service, self._llm_service)
        self._agent = create_react_agent(self._llm, tools, prompt=_SYSTEM_PROMPT)

    async def query(self, request: AgentQuery) -> AgentResponse:
        query = request.query
        if request.patient_id:
            query = f"[Patient ID: {request.patient_id}] {query}"

        logger.info("agent_query", query=request.query, patient_id=request.patient_id)

        result = await self._agent.ainvoke({"messages": [HumanMessage(content=query)]})
        answer = result["messages"][-1].content
        return AgentResponse(answer=answer)
