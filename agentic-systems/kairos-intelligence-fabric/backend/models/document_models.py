from __future__ import annotations

from pydantic import BaseModel, Field


class DocumentModel(BaseModel):
    id: str
    title: str
    filename: str
    content_preview: str = ""
    uploaded_at: str = ""
    status: str = "uploaded"  # uploaded | ingesting | ingested | error
    size_bytes: int = 0


class DocumentUploadResponse(BaseModel):
    id: str
    title: str
    filename: str
    status: str


class DocumentListResponse(BaseModel):
    documents: list[DocumentModel]
    total: int
