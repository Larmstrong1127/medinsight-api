"""
Seed the local document store with synthetic clinical notes for development.
Usage: python synthetic_data/seed.py
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.models.document import DocumentCreate, DocumentType
from app.services.document_service import DocumentService


def main() -> None:
    notes_path = Path(__file__).parent / "sample_notes.json"
    notes = json.loads(notes_path.read_text())

    service = DocumentService()
    for note in notes:
        doc = service.create(
            DocumentCreate(
                content=note["content"],
                patient_id=note["patient_id"],
                document_type=DocumentType(note["document_type"]),
            )
        )
        print(f"Created: {doc.id} | patient={doc.patient_id} | type={doc.document_type}")

    print(f"\nSeeded {len(notes)} synthetic documents.")


if __name__ == "__main__":
    main()
