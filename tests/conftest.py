import pytest
from fastapi.testclient import TestClient

from app.main import create_app


@pytest.fixture(scope="session")
def app():
    return create_app()


@pytest.fixture(scope="session")
def client(app):
    return TestClient(app)


@pytest.fixture
def auth_headers():
    return {"X-API-Key": "dev-key-change-me-in-production"}


@pytest.fixture
def sample_document_payload():
    return {
        "content": (
            "Patient: John Doe, DOB: 01/01/1960. "
            "Chief complaint: chest pain and shortness of breath for 2 days. "
            "History: Type 2 diabetes mellitus, hypertension. "
            "Medications: Metformin 1000mg BID, Lisinopril 10mg daily. "
            "Assessment: Possible acute coronary syndrome. "
            "Plan: Admit for cardiac workup, troponin q6h, ECG, cardiology consult."
        ),
        "patient_id": "pt-test-001",
        "document_type": "admission_note",
        "metadata": {"facility": "test-hospital", "department": "emergency"},
    }
