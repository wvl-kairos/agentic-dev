"""Webhook endpoints for external integrations (Fireflies, CoderPad)."""

import logging

from fastapi import APIRouter, BackgroundTasks, Request

from talentlens.dependencies import DBSession

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/webhooks", tags=["webhooks"])


@router.post("/fireflies")
async def fireflies_webhook(request: Request, bg: BackgroundTasks, db: DBSession):
    """Receive Fireflies transcript webhook. Validates signature, ingests transcript,
    triggers assessment pipeline via BackgroundTasks."""
    # TODO: validate webhook signature
    # TODO: parse payload, create Interview record
    # TODO: bg.add_task(run_assessment_pipeline, interview_id)
    return {"status": "accepted"}


@router.post("/coderpad")
async def coderpad_webhook(request: Request, bg: BackgroundTasks, db: DBSession):
    """Receive CoderPad challenge results."""
    # TODO: parse payload, update candidate stage + create assessment
    return {"status": "accepted"}
