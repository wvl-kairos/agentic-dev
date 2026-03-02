from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path

from config import settings
from models.document_models import DocumentModel

logger = logging.getLogger(__name__)

UPLOADS_DIR = Path(__file__).parent.parent / "data" / "uploads"
SAMPLE_DOCS_DIR = Path(__file__).parent.parent / "data" / "documents"
REFERENCE_SCHEMAS_DIR = Path(__file__).parent.parent / "data" / "reference_schemas"
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)

SUPPORTED_EXTENSIONS = ("*.txt", "*.md", "*.csv", "*.json", "*.sql")


class DocumentManager:
    """Manages document storage and metadata.

    When Neo4j is enabled, document metadata is stored as (:Document) nodes.
    Otherwise, uses a simple in-memory dict.
    """

    def __init__(self) -> None:
        self._docs: dict[str, DocumentModel] = {}
        self._load_sample_docs()
        self._load_reference_schemas()

    def _load_sample_docs(self) -> None:
        """Pre-load sample documents from data/documents/."""
        if not SAMPLE_DOCS_DIR.exists():
            return
        for ext_pattern in SUPPORTED_EXTENSIONS:
            for path in sorted(SAMPLE_DOCS_DIR.glob(ext_pattern)):
                doc_id = f"doc-{path.stem.replace('_', '-')}"
                if doc_id in self._docs:
                    continue
                title = path.stem.replace("_", " ").title()
                content = path.read_text(encoding="utf-8", errors="replace")
                self._docs[doc_id] = DocumentModel(
                    id=doc_id,
                    title=title,
                    filename=path.name,
                    content_preview=content[:200] + "..." if len(content) > 200 else content,
                    uploaded_at="2026-02-19T00:00:00Z",
                    status="uploaded",
                    size_bytes=path.stat().st_size,
                )
        logger.info("Loaded %d sample documents", len(self._docs))

    def _load_reference_schemas(self) -> None:
        """Pre-load reference schema documents from data/reference_schemas/."""
        if not REFERENCE_SCHEMAS_DIR.exists():
            return
        count = 0
        for ext_pattern in SUPPORTED_EXTENSIONS:
            for path in sorted(REFERENCE_SCHEMAS_DIR.glob(ext_pattern)):
                doc_id = f"ref-{path.stem.replace('_', '-')}"
                if doc_id in self._docs:
                    continue
                title = path.stem.replace("_", " ").title()
                content = path.read_text(encoding="utf-8", errors="replace")
                self._docs[doc_id] = DocumentModel(
                    id=doc_id,
                    title=title,
                    filename=path.name,
                    content_preview=content[:200] + "..." if len(content) > 200 else content,
                    uploaded_at="2026-02-19T00:00:00Z",
                    status="uploaded",
                    size_bytes=path.stat().st_size,
                )
                count += 1
        if count:
            logger.info("Loaded %d reference schema documents", count)

    def list_documents(self) -> list[DocumentModel]:
        return list(self._docs.values())

    def get_document(self, doc_id: str) -> DocumentModel | None:
        return self._docs.get(doc_id)

    def get_document_content(self, doc_id: str) -> str | None:
        doc = self._docs.get(doc_id)
        if not doc:
            return None
        # Check uploads first, then sample docs, then reference schemas
        upload_path = UPLOADS_DIR / doc.filename
        if upload_path.exists():
            return upload_path.read_text(encoding="utf-8", errors="replace")
        sample_path = SAMPLE_DOCS_DIR / doc.filename
        if sample_path.exists():
            return sample_path.read_text(encoding="utf-8", errors="replace")
        ref_path = REFERENCE_SCHEMAS_DIR / doc.filename
        if ref_path.exists():
            return ref_path.read_text(encoding="utf-8", errors="replace")
        return None

    async def save_uploaded_file(self, filename: str, content: bytes) -> DocumentModel:
        doc_id = f"doc-{uuid.uuid4().hex[:8]}"
        save_path = UPLOADS_DIR / Path(filename).name
        save_path.write_bytes(content)

        text_content = content.decode("utf-8", errors="replace")
        title = Path(filename).stem.replace("_", " ").replace("-", " ").title()

        doc = DocumentModel(
            id=doc_id,
            title=title,
            filename=Path(filename).name,
            content_preview=text_content[:200] + "..." if len(text_content) > 200 else text_content,
            uploaded_at=datetime.now(timezone.utc).isoformat(),
            status="uploaded",
            size_bytes=len(content),
        )
        self._docs[doc_id] = doc

        if settings.neo4j_enabled:
            await self._save_to_neo4j(doc)

        logger.info("Saved document: %s (%s)", doc_id, filename)
        return doc

    def update_status(self, doc_id: str, status: str) -> None:
        if doc_id in self._docs:
            self._docs[doc_id].status = status

    async def _save_to_neo4j(self, doc: DocumentModel) -> None:
        from services.neo4j_connection import get_driver

        driver = await get_driver()
        async with driver.session() as session:
            await session.run(
                """
                MERGE (d:Document {id: $id})
                SET d.title = $title,
                    d.filename = $filename,
                    d.uploaded_at = $uploaded_at,
                    d.status = $status,
                    d.type = 'document',
                    d.label = $title,
                    d.size_bytes = $size_bytes
                """,
                {
                    "id": doc.id,
                    "title": doc.title,
                    "filename": doc.filename,
                    "uploaded_at": doc.uploaded_at,
                    "status": doc.status,
                    "size_bytes": doc.size_bytes,
                },
            )


# Singleton
document_manager = DocumentManager()
