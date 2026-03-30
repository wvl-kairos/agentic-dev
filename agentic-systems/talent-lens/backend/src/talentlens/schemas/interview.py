import uuid
from datetime import datetime

from pydantic import BaseModel

from talentlens.models.database.interview import InterviewType


class InterviewResponse(BaseModel):
    id: uuid.UUID
    candidate_id: uuid.UUID
    interview_type: InterviewType
    source: str | None
    talk_ratio: float | None
    duration_seconds: int | None
    recording_url: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class InterviewDetailResponse(InterviewResponse):
    """Extended response including transcript text."""

    transcript: str | None = None


class InterviewListResponse(BaseModel):
    """Interview list item with candidate name for the interviews page."""

    id: uuid.UUID
    candidate_id: uuid.UUID | None
    candidate_name: str | None = None
    interview_type: InterviewType
    source: str | None
    talk_ratio: float | None
    duration_seconds: int | None
    recording_url: str | None = None
    created_at: datetime
    overall_score: float | None = None
    recommendation: str | None = None
    transcript_preview: str | None = None
    assessment_id: uuid.UUID | None = None

    model_config = {"from_attributes": True}
