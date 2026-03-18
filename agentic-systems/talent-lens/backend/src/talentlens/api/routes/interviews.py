"""Interview endpoints — manual ingestion and results."""

import logging
import uuid

from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel
from sqlalchemy import select

from talentlens.dependencies import DBSession
from talentlens.models.database.candidate import Candidate
from talentlens.models.database.interview import Interview, InterviewType
from talentlens.schemas.interview import InterviewResponse
from talentlens.services.assessment.talk_ratio import compute_talk_ratio, parse_transcript_to_segments
from talentlens.tasks.assessment import process_interview

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/interviews", tags=["interviews"])


class ManualInterviewCreate(BaseModel):
    """For manual transcript ingestion (testing, non-Fireflies sources)."""

    candidate_id: uuid.UUID | None = None
    interview_type: InterviewType = InterviewType.technical
    transcript: str
    diarization: list[dict] | None = None
    source: str = "manual"


@router.post("/", status_code=201)
async def create_interview(data: ManualInterviewCreate, bg: BackgroundTasks, db: DBSession):
    """Manually create an interview with transcript. Triggers analysis pipeline."""
    interview = Interview(
        candidate_id=data.candidate_id,
        interview_type=data.interview_type,
        source=data.source,
        transcript=data.transcript,
        diarization=data.diarization or [],
    )
    db.add(interview)
    await db.commit()
    await db.refresh(interview)

    # Run analysis in background
    bg.add_task(process_interview, interview.id)

    return {
        "id": str(interview.id),
        "status": "processing",
        "message": "Interview created, analysis running in background",
    }


@router.get("/candidate/{candidate_id}", response_model=list[InterviewResponse])
async def list_candidate_interviews(candidate_id: uuid.UUID, db: DBSession):
    result = await db.execute(
        select(Interview)
        .where(Interview.candidate_id == candidate_id)
        .order_by(Interview.created_at)
    )
    return result.scalars().all()


@router.get("/{interview_id}")
async def get_interview(interview_id: uuid.UUID, db: DBSession):
    """Get interview with full analysis results."""
    interview = await db.get(Interview, interview_id)
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")
    return {
        "id": str(interview.id),
        "candidate_id": str(interview.candidate_id) if interview.candidate_id else None,
        "interview_type": interview.interview_type.value,
        "source": interview.source,
        "talk_ratio": interview.talk_ratio,
        "duration_seconds": interview.duration_seconds,
        "recording_url": interview.recording_url,
        "diarization": interview.diarization,
        "transcript": interview.transcript,
        "transcript_length": len(interview.transcript) if interview.transcript else 0,
        "created_at": interview.created_at.isoformat(),
    }


@router.post("/recompute-talk-ratios")
async def recompute_talk_ratios(db: DBSession):
    """Re-compute talk ratios for all interviews where ratio is 0 or null.

    This fixes interviews processed before the transcript parser was added.
    Interviews without speaker labels get talk_ratio set to NULL (not 0.0).
    """
    result = await db.execute(
        select(Interview).where(
            Interview.transcript.isnot(None),
            (Interview.talk_ratio == 0) | (Interview.talk_ratio.is_(None)),
        )
    )
    interviews = result.scalars().all()
    updated = 0
    set_null = 0

    for interview in interviews:
        # Try diarization segments first
        diarization = interview.diarization
        if isinstance(diarization, dict):
            segments = diarization.get("segments", [])
        else:
            segments = diarization or []

        # Fall back to transcript parsing
        if not segments and interview.transcript:
            segments = parse_transcript_to_segments(interview.transcript)

        if not segments:
            # No speaker labels — set to NULL instead of 0.0
            if interview.talk_ratio == 0:
                interview.talk_ratio = None
                set_null += 1
            continue

        # Get candidate name for speaker identification
        candidate_name = None
        if interview.candidate_id:
            candidate = await db.get(Candidate, interview.candidate_id)
            if candidate:
                candidate_name = candidate.name

        talk_result = compute_talk_ratio(segments, candidate_name)
        new_ratio = talk_result["candidate_ratio"]

        if new_ratio > 0:
            interview.talk_ratio = new_ratio
            # Also store parsed segments in diarization if it was empty
            if not interview.diarization or (isinstance(interview.diarization, list) and len(interview.diarization) == 0):
                interview.diarization = {
                    "segments": segments,
                    "analysis": {"talk_ratio": talk_result},
                }
            updated += 1
            logger.info(
                "Recomputed talk ratio for interview %s: %.0f%%",
                interview.id, new_ratio * 100,
            )

    await db.commit()
    return {"updated": updated, "set_null": set_null, "total_checked": len(interviews)}
