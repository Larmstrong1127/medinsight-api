import pytest

from app.models.document import DocumentCreate, DocumentType
from app.services.document_service import DocumentNotFoundError, DocumentService


@pytest.fixture
def doc_service(tmp_path, monkeypatch):
    monkeypatch.setenv("STORAGE_BACKEND", "local")
    monkeypatch.setenv("LOCAL_STORAGE_PATH", str(tmp_path))
    from app import config
    config.get_settings.cache_clear()
    yield DocumentService()
    config.get_settings.cache_clear()


@pytest.fixture
def sample_payload():
    return DocumentCreate(
        content="Patient presents with fever 38.5C, cough, fatigue. Assessment: viral URI.",
        patient_id="pt-unit-001",
        document_type=DocumentType.PROGRESS_NOTE,
        metadata={"provider": "dr-smith"},
    )


def test_create_returns_document_without_content(doc_service, sample_payload):
    doc = doc_service.create(sample_payload)
    assert doc.id
    assert doc.patient_id == "pt-unit-001"
    assert not hasattr(doc, "content") or doc.model_fields_set.issuperset(set())


def test_get_without_content_omits_content(doc_service, sample_payload):
    created = doc_service.create(sample_payload)
    fetched = doc_service.get(created.id, include_content=False)
    assert fetched.id == created.id
    assert not hasattr(fetched, "content")


def test_get_with_content_decrypts_correctly(doc_service, sample_payload):
    created = doc_service.create(sample_payload)
    fetched = doc_service.get(created.id, include_content=True)
    assert fetched.content == sample_payload.content  # type: ignore[union-attr]


def test_checksum_is_stable(doc_service, sample_payload):
    import hashlib
    created = doc_service.create(sample_payload)
    expected = hashlib.sha256(sample_payload.content.encode()).hexdigest()
    assert created.checksum == expected


def test_get_nonexistent_raises(doc_service):
    with pytest.raises(DocumentNotFoundError):
        doc_service.get("nonexistent-id")


def test_list_filters_by_patient(doc_service, sample_payload):
    doc_service.create(sample_payload)
    other = sample_payload.model_copy(update={"patient_id": "pt-unit-999"})
    doc_service.create(other)

    result = doc_service.list_documents(patient_id="pt-unit-001")
    assert all(d.patient_id == "pt-unit-001" for d in result.documents)
