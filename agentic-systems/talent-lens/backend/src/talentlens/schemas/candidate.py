import uuid
from datetime import datetime

from pydantic import BaseModel

from talentlens.models.database.candidate import PipelineStage


class CandidateCreate(BaseModel):
    venture_id: uuid.UUID
    name: str
    email: str | None = None
    role: str | None = None


class CandidateUpdate(BaseModel):
    name: str | None = None
    email: str | None = None
    role: str | None = None
    stage: PipelineStage | None = None
    notes: str | None = None


class CandidateResponse(BaseModel):
    id: uuid.UUID
    venture_id: uuid.UUID
    name: str
    email: str | None
    role: str | None
    stage: PipelineStage
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
