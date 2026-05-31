

def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "timestamp" in data


def test_create_document_requires_auth(client, sample_document_payload):
    response = client.post("/api/v1/documents", json=sample_document_payload)
    assert response.status_code == 401


def test_create_document(client, auth_headers, sample_document_payload, tmp_path, monkeypatch):
    monkeypatch.setenv("LOCAL_STORAGE_PATH", str(tmp_path))
    from app import config
    config.get_settings.cache_clear()

    response = client.post(
        "/api/v1/documents",
        json=sample_document_payload,
        headers=auth_headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["patient_id"] == sample_document_payload["patient_id"]
    assert "id" in data
    assert "content" not in data  # content must never be in default response


def test_get_document_not_found(client, auth_headers):
    response = client.get("/api/v1/documents/nonexistent", headers=auth_headers)
    assert response.status_code == 404


def test_list_documents(client, auth_headers, sample_document_payload, tmp_path, monkeypatch):
    monkeypatch.setenv("LOCAL_STORAGE_PATH", str(tmp_path))
    from app import config
    config.get_settings.cache_clear()

    client.post("/api/v1/documents", json=sample_document_payload, headers=auth_headers)
    response = client.get("/api/v1/documents", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["total"] >= 1


def test_audit_logs_require_auth(client):
    response = client.get("/api/v1/audit/logs")
    assert response.status_code == 401


def test_audit_logs_accessible(client, auth_headers, tmp_path, monkeypatch):
    monkeypatch.setenv("LOCAL_STORAGE_PATH", str(tmp_path))
    from app import config
    config.get_settings.cache_clear()

    response = client.get("/api/v1/audit/logs", headers=auth_headers)
    assert response.status_code == 200
    assert "logs" in response.json()


def test_request_id_header_echoed(client, auth_headers):
    response = client.get("/health", headers={**auth_headers, "X-Request-ID": "test-123"})
    assert response.headers.get("X-Request-ID") == "test-123"
