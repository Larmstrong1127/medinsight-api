from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain.tools import tool
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
from pydantic import BaseModel

from app.config import get_settings
from app.core.logging import get_logger
from app.services.document_service import DocumentService
from app.services.llm_service import LLMService
from app.models.analysis import AnalysisRequest, AnalysisType

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
    def get_document_summary(document_id: str) -> str:
        """Retrieve and summarize a specific clinical document by its ID."""
        import asyncio

        request = AnalysisRequest(
            document_id=document_id,
            analysis_type=AnalysisType.SUMMARIZE,
        )
        analysis = asyncio.get_event_loop().run_until_complete(llm_service.analyze(request))
        return analysis.result.summary or "No summary available."

    @tool
    def extract_diagnoses_from_document(document_id: str) -> str:
        """Extract diagnoses from a specific clinical document."""
        import asyncio

        request = AnalysisRequest(
            document_id=document_id,
            analysis_type=AnalysisType.EXTRACT_DIAGNOSES,
        )
        analysis = asyncio.get_event_loop().run_until_complete(llm_service.analyze(request))
        if not analysis.result.diagnoses:
            return "No diagnoses extracted."
        return "\n".join(
            f"- {d.description} (confidence: {d.confidence:.0%})"
            for d in analysis.result.diagnoses
        )

    @tool
    def assess_patient_risk(document_id: str) -> str:
        """Perform a risk assessment on a clinical document."""
        import asyncio

        request = AnalysisRequest(
            document_id=document_id,
            analysis_type=AnalysisType.RISK_ASSESSMENT,
        )
        analysis = asyncio.get_event_loop().run_until_complete(llm_service.analyze(request))
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
If a patient_id is provided, scope your searches to that patient."""


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
        self._executor = self._build_executor()

    def _build_executor(self) -> AgentExecutor:
        tools = _make_tools(self._doc_service, self._llm_service)
        prompt = ChatPromptTemplate.from_messages([
            ("system", _SYSTEM_PROMPT),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])
        agent = create_openai_functions_agent(self._llm, tools, prompt)
        return AgentExecutor(agent=agent, tools=tools, verbose=False, max_iterations=5)

    async def query(self, request: AgentQuery) -> AgentResponse:
        query = request.query
        if request.patient_id:
            query = f"[Patient ID: {request.patient_id}] {query}"

        logger.info("agent_query", query=request.query, patient_id=request.patient_id)

        result = await self._executor.ainvoke({"input": query})
        return AgentResponse(answer=result["output"])
