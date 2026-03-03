"""Webhook endpoints for external integrations (Fireflies, CoderPad)."""

import logging
import uuid

from fastapi import APIRouter, BackgroundTasks, HTTPException, Request
from pydantic import BaseModel

from talentlens.config import settings
from talentlens.dependencies import DBSession
from talentlens.models.database.interview import InterviewType
from talentlens.services.ingestion.fireflies import (
    ingest_fireflies_transcript,
    validate_webhook_signature,
)
from talentlens.tasks.assessment import process_interview

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/webhooks", tags=["webhooks"])


class FirefliesWebhookPayload(BaseModel):
    meetingId: str
    eventType: str = ""
    clientReferenceId: str | None = None
    # We add these for linking to a candidate (sent as query params or custom fields)
    candidate_id: uuid.UUID | None = None
    interview_type: str = "technical"


@router.post("/fireflies")
async def fireflies_webhook(request: Request, bg: BackgroundTasks, db: DBSession):
    """Receive Fireflies transcript webhook.

    Fireflies sends {meetingId, eventType} when transcription completes.
    We validate the signature, then fetch the full transcript via GraphQL.
    """
    body = await request.body()

    # Validate signature
    signature = request.headers.get("x-hub-signature", "")
    if settings.fireflies_webhook_secret and not validate_webhook_signature(
        body, signature, settings.fireflies_webhook_secret
    ):
        raise HTTPException(status_code=401, detail="Invalid webhook signature")

    payload = FirefliesWebhookPayload.model_validate_json(body)

    if payload.eventType and payload.eventType != "Transcription completed":
        logger.info("Ignoring Fireflies event: %s", payload.eventType)
        return {"status": "ignored", "event": payload.eventType}

    if not payload.candidate_id:
        logger.warning(
            "Fireflies webhook for meeting %s has no candidate_id — storing for manual linking",
            payload.meetingId,
        )

    # Map string to enum
    interview_type_map = {
        "screening": InterviewType.screening,
        "technical": InterviewType.technical,
        "final": InterviewType.final,
    }
    itype = interview_type_map.get(payload.interview_type, InterviewType.technical)

    # Ingest transcript (creates Interview record)
    interview = await ingest_fireflies_transcript(
        meeting_id=payload.meetingId,
        candidate_id=payload.candidate_id,
        interview_type=itype,
        db=db,
    )

    # Run analysis in background
    bg.add_task(process_interview, interview.id)

    return {
        "status": "accepted",
        "interview_id": str(interview.id),
        "meeting_id": payload.meetingId,
    }


@router.post("/coderpad")
async def coderpad_webhook(request: Request, bg: BackgroundTasks, db: DBSession):
    """Receive CoderPad challenge results."""
    # TODO: parse payload, update candidate stage + create assessment
    return {"status": "accepted"}
