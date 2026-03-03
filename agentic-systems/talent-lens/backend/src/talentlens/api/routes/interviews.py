"""Interview endpoints — manual ingestion and results."""

import uuid

from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel
from sqlalchemy import select

from talentlens.dependencies import DBSession
from talentlens.models.database.interview import Interview, InterviewType
from talentlens.schemas.interview import InterviewResponse
from talentlens.tasks.assessment import process_interview

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
        "diarization": interview.diarization,
        "transcript_length": len(interview.transcript) if interview.transcript else 0,
        "created_at": interview.created_at.isoformat(),
    }
