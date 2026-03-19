"""Schemas for in-platform capabilities survey."""

import uuid
from datetime import datetime

from pydantic import BaseModel


class SurveyAnswerCreate(BaseModel):
    capability_id: uuid.UUID
    score: int  # 1-10


class SurveyCreate(BaseModel):
    respondent_name: str
    respondent_email: str | None = None
    answers: list[SurveyAnswerCreate]


class SurveyAnswerResponse(BaseModel):
    id: uuid.UUID
    capability_id: uuid.UUID
    score: int
    created_at: datetime

    model_config = {"from_attributes": True}


class SurveyResponseResponse(BaseModel):
    id: uuid.UUID
    role_template_id: uuid.UUID
    respondent_name: str
    respondent_email: str | None
    completed_at: datetime | None
    created_at: datetime
    answers: list[SurveyAnswerResponse] = []

    model_config = {"from_attributes": True}


class SurveyAggregateScore(BaseModel):
    capability_id: uuid.UUID
    capability_name: str
    avg_score: float
    response_count: int
