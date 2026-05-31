import pytest

from app.models.audit import AuditAction, AuditOutcome
from app.services.audit_service import AuditService


@pytest.fixture
def audit_service(tmp_path, monkeypatch):
    monkeypatch.setenv("STORAGE_BACKEND", "local")
    monkeypatch.setenv("LOCAL_STORAGE_PATH", str(tmp_path))
    from app import config
    config.get_settings.cache_clear()
    yield AuditService()
    config.get_settings.cache_clear()


def test_record_creates_log_entry(audit_service):
    log = audit_service.record(
        action=AuditAction.DOCUMENT_CREATE,
        request_id="req-001",
        ip_address="127.0.0.1",
        api_key="dev-key-change-me-in-production",
        outcome=AuditOutcome.SUCCESS,
        resource_id="doc-abc",
    )
    assert log.id
    assert log.action == AuditAction.DOCUMENT_CREATE
    assert log.outcome == AuditOutcome.SUCCESS
    assert log.resource_id == "doc-abc"
    assert log.request_id == "req-001"


def test_record_masks_api_key(audit_service):
    log = audit_service.record(
        action=AuditAction.DOCUMENT_READ,
        request_id="req-002",
        ip_address="127.0.0.1",
        api_key="dev-key-change-me-in-production",
        outcome=AuditOutcome.SUCCESS,
    )
    # Only the first 8 chars should be stored
    assert log.api_key_prefix == "dev-key-"
    assert "change-me" not in log.api_key_prefix


def test_record_persists_to_disk(audit_service, tmp_path):
    audit_service.record(
        action=AuditAction.DOCUMENT_LIST,
        request_id="req-003",
        ip_address="10.0.0.1",
        api_key="dev-key-change-me-in-production",
        outcome=AuditOutcome.SUCCESS,
    )
    log_file = tmp_path / "audit_logs.jsonl"
    assert log_file.exists()
    assert log_file.stat().st_size > 0


def test_list_logs_empty_when_no_logs(audit_service):
    result = audit_service.list_logs()
    assert result.total == 0
    assert result.logs == []


def test_list_logs_returns_recorded_entries(audit_service):
    for i in range(3):
        audit_service.record(
            action=AuditAction.DOCUMENT_READ,
            request_id=f"req-{i}",
            ip_address="127.0.0.1",
            api_key="dev-key-change-me-in-production",
            outcome=AuditOutcome.SUCCESS,
            resource_id=f"doc-{i}",
        )

    result = audit_service.list_logs()
    assert result.total == 3
    assert len(result.logs) == 3


def test_list_logs_respects_limit(audit_service):
    for i in range(5):
        audit_service.record(
            action=AuditAction.DOCUMENT_READ,
            request_id=f"req-{i}",
            ip_address="127.0.0.1",
            api_key="dev-key-change-me-in-production",
            outcome=AuditOutcome.SUCCESS,
        )

    result = audit_service.list_logs(limit=2)
    assert len(result.logs) == 2
    assert result.total == 5


def test_record_failure_outcome(audit_service):
    log = audit_service.record(
        action=AuditAction.DOCUMENT_READ,
        request_id="req-fail",
        ip_address="127.0.0.1",
        api_key="dev-key-change-me-in-production",
        outcome=AuditOutcome.FAILURE,
        resource_id="missing-doc",
        detail="not_found",
    )
    assert log.outcome == AuditOutcome.FAILURE
    assert log.detail == "not_found"
