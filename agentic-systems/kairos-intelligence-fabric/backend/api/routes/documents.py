from fastapi import APIRouter, HTTPException, UploadFile, File

from models.document_models import DocumentListResponse, DocumentModel, DocumentUploadResponse
from services.document_manager import document_manager

router = APIRouter()


@router.get("/documents", response_model=DocumentListResponse)
async def list_documents():
    docs = document_manager.list_documents()
    return DocumentListResponse(documents=docs, total=len(docs))


@router.get("/documents/{doc_id}", response_model=DocumentModel)
async def get_document(doc_id: str):
    doc = document_manager.get_document(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc


@router.get("/documents/{doc_id}/content")
async def get_document_content(doc_id: str):
    content = document_manager.get_document_content(doc_id)
    if content is None:
        raise HTTPException(status_code=404, detail="Document not found")
    return {"id": doc_id, "content": content}


@router.post("/documents/upload", response_model=DocumentUploadResponse)
async def upload_document(file: UploadFile = File(...)):
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")

    content = await file.read()
    if len(content) > 10 * 1024 * 1024:  # 10 MB limit
        raise HTTPException(status_code=413, detail="File too large (max 10 MB)")

    doc = await document_manager.save_uploaded_file(file.filename, content)
    return DocumentUploadResponse(
        id=doc.id,
        title=doc.title,
        filename=doc.filename,
        status=doc.status,
    )
