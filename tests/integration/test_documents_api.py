"""
Extended integration tests for the Documents API.
Covers content retrieval, patient filtering, invalid auth, and edge cases.
"""
import pytest


@pytest.fixture
def isolated_client(tmp_path, monkeypatch):
    """Client with isolated local storage so tests don't share state."""
    import os

    from cryptography.fernet import Fernet
    monkeypatch.setenv("STORAGE_BACKEND", "local")
    monkeypatch.setenv("LOCAL_STORAGE_PATH", str(tmp_path))
    monkeypatch.setenv("ENCRYPTION_KEY", Fernet.generate_key().decode())
    # Ensure the valid API key matches what the auth fixture provides
    api_key = os.environ.get("API_KEYS", "dev-key-change-me-in-production")
    monkeypatch.setenv("API_KEYS", api_key)
    from app import config
    config.get_settings.cache_clear()

    from fastapi.testclient import TestClient

    from app.main import create_app
    with TestClient(create_app()) as c:
        yield c

    config.get_settings.cache_clear()


@pytest.fixture
def auth():
    import os
    key = os.environ.get("API_KEYS", "dev-key-change-me-in-production").split(",")[0].strip()
    return {"X-API-Key": key}


@pytest.fixture
def doc_payload():
    return {
        "content": "Patient: Jane Smith. Chief complaint: headache for 3 days. Assessment: tension headache.",
        "patient_id": "pt-jane-001",
        "document_type": "progress_note",
        "metadata": {"department": "neurology"},
    }


# ─────────────────────────────────────────────
# Authentication
# ─────────────────────────────────────────────
class TestAuthentication:
    def test_invalid_api_key_rejected(self, isolated_client, doc_payload):
        res = isolated_client.post(
            "/api/v1/documents",
            json=doc_payload,
            headers={"X-API-Key": "totally-wrong-key"},
        )
        assert res.status_code == 401

    def test_missing_api_key_rejected(self, isolated_client, doc_payload):
        res = isolated_client.post("/api/v1/documents", json=doc_payload)
        assert res.status_code == 401

    def test_list_requires_auth(self, isolated_client):
        res = isolated_client.get("/api/v1/documents")
        assert res.status_code == 401

    def test_get_requires_auth(self, isolated_client):
        res = isolated_client.get("/api/v1/documents/some-id")
        assert res.status_code == 401


# ─────────────────────────────────────────────
# Document CRUD
# ─────────────────────────────────────────────
class TestDocumentCRUD:
    def test_create_returns_201_with_id(self, isolated_client, auth, doc_payload):
        res = isolated_client.post("/api/v1/documents", json=doc_payload, headers=auth)
        assert res.status_code == 201
        data = res.json()
        assert "id" in data
        assert data["patient_id"] == doc_payload["patient_id"]

    def test_create_does_not_expose_content(self, isolated_client, auth, doc_payload):
        res = isolated_client.post("/api/v1/documents", json=doc_payload, headers=auth)
        assert res.status_code == 201
        assert "content" not in res.json()

    def test_get_document_by_id(self, isolated_client, auth, doc_payload):
        create_res = isolated_client.post("/api/v1/documents", json=doc_payload, headers=auth)
        doc_id = create_res.json()["id"]

        get_res = isolated_client.get(f"/api/v1/documents/{doc_id}", headers=auth)
        assert get_res.status_code == 200
        assert get_res.json()["id"] == doc_id

    def test_get_document_with_content_decrypts(self, isolated_client, auth, doc_payload):
        create_res = isolated_client.post("/api/v1/documents", json=doc_payload, headers=auth)
        doc_id = create_res.json()["id"]

        get_res = isolated_client.get(
            f"/api/v1/documents/{doc_id}",
            params={"include_content": True},
            headers=auth,
        )
        assert get_res.status_code == 200
        assert get_res.json()["content"] == doc_payload["content"]

    def test_get_nonexistent_returns_404(self, isolated_client, auth):
        res = isolated_client.get("/api/v1/documents/does-not-exist", headers=auth)
        assert res.status_code == 404
        assert "not found" in res.json()["detail"].lower()

    def test_checksum_present_in_response(self, isolated_client, auth, doc_payload):
        res = isolated_client.post("/api/v1/documents", json=doc_payload, headers=auth)
        assert "checksum" in res.json()

    def test_document_type_stored_correctly(self, isolated_client, auth, doc_payload):
        res = isolated_client.post("/api/v1/documents", json=doc_payload, headers=auth)
        assert res.json()["document_type"] == doc_payload["document_type"]


# ─────────────────────────────────────────────
# Document Listing & Filtering
# ─────────────────────────────────────────────
class TestDocumentListing:
    def test_list_returns_all_documents(self, isolated_client, auth, doc_payload):
        isolated_client.post("/api/v1/documents", json=doc_payload, headers=auth)
        isolated_client.post("/api/v1/documents", json=doc_payload, headers=auth)

        res = isolated_client.get("/api/v1/documents", headers=auth)
        assert res.status_code == 200
        assert res.json()["total"] == 2

    def test_list_filters_by_patient_id(self, isolated_client, auth, doc_payload):
        # Create doc for patient A
        isolated_client.post("/api/v1/documents", json=doc_payload, headers=auth)

        # Create doc for patient B
        other_payload = {**doc_payload, "patient_id": "pt-other-999"}
        isolated_client.post("/api/v1/documents", json=other_payload, headers=auth)

        res = isolated_client.get(
            "/api/v1/documents",
            params={"patient_id": "pt-jane-001"},
            headers=auth,
        )
        assert res.status_code == 200
        data = res.json()
        assert data["total"] == 1
        assert all(d["patient_id"] == "pt-jane-001" for d in data["documents"])

    def test_list_empty_when_no_documents(self, isolated_client, auth):
        res = isolated_client.get("/api/v1/documents", headers=auth)
        assert res.status_code == 200
        assert res.json()["total"] == 0


# ─────────────────────────────────────────────
# Audit trail
# ─────────────────────────────────────────────
class TestAuditTrail:
    def test_create_document_writes_audit_log(self, isolated_client, auth, doc_payload):
        isolated_client.post("/api/v1/documents", json=doc_payload, headers=auth)

        audit_res = isolated_client.get("/api/v1/audit/logs", headers=auth)
        assert audit_res.status_code == 200
        logs = audit_res.json()["logs"]
        actions = [log["action"] for log in logs]
        assert "document.create" in actions

    def test_failed_get_writes_failure_audit(self, isolated_client, auth):
        isolated_client.get("/api/v1/documents/nonexistent", headers=auth)

        audit_res = isolated_client.get("/api/v1/audit/logs", headers=auth)
        logs = audit_res.json()["logs"]
        failure_logs = [log for log in logs if log["outcome"] == "failure"]
        assert len(failure_logs) >= 1
