from fastapi import APIRouter, BackgroundTasks, HTTPException

from models.ingestion_models import IngestionResult, IngestionStatusResponse
from services.document_manager import document_manager
from services.ingestion_pipeline import get_ingestion_status, run_ingestion

router = APIRouter()


@router.post("/ingest/{doc_id}", response_model=IngestionStatusResponse)
async def ingest_document(doc_id: str, background_tasks: BackgroundTasks):
    doc = document_manager.get_document(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    if doc.status == "ingesting":
        raise HTTPException(status_code=409, detail="Document is already being ingested")

    if doc.status == "ingested":
        existing = get_ingestion_status(doc_id)
        if existing:
            return IngestionStatusResponse(
                document_id=doc_id,
                status="completed",
                result=existing,
            )

    # Run ingestion in background
    background_tasks.add_task(run_ingestion, doc_id)

    return IngestionStatusResponse(
        document_id=doc_id,
        status="processing",
        result=None,
    )


@router.get("/ingest/{doc_id}/status", response_model=IngestionStatusResponse)
async def get_ingest_status(doc_id: str):
    doc = document_manager.get_document(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    result = get_ingestion_status(doc_id)
    status = result.status if result else "not_started"

    return IngestionStatusResponse(
        document_id=doc_id,
        status=status,
        result=result,
    )
