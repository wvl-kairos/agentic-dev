"""Ontology construction API routes.

POST /api/ontology/construct — SSE stream of ontology construction events
GET  /api/ontology/status   — Current construction status
"""

from __future__ import annotations

import json
import logging

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from models.ontology_models import OntologyConstructRequest, OntologyConstructStatus

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/ontology/construct")
async def construct_ontology(request: OntologyConstructRequest):
    """Construct ontology from schema documents.

    Returns a Server-Sent Events (SSE) stream with construction progress.
    Each event is a JSON object with: event, phase, data.

    Frontend should consume with EventSource or fetch + ReadableStream.
    """
    from services.ontology_engine import construct_ontology as run_construction

    async def event_stream():
        try:
            async for event in run_construction(
                document_ids=request.document_ids or None,
                include_sample=request.include_sample_ontology,
            ):
                payload = event.model_dump()
                yield f"event: {event.event}\ndata: {json.dumps(payload)}\n\n"
        except Exception as e:
            logger.error("SSE stream failed: %s", e, exc_info=True)
            yield f"event: error\ndata: {json.dumps({'message': str(e)})}\n\n"

        yield "event: done\ndata: {}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/ontology/status", response_model=OntologyConstructStatus)
async def get_ontology_status():
    """Get current ontology construction status."""
    from services.ontology_engine import get_construction_status

    return get_construction_status()
