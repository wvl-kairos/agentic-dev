import uuid
from datetime import datetime

from pydantic import BaseModel

from talentlens.models.database.candidate import PipelineStage


class CandidateCreate(BaseModel):
    venture_id: uuid.UUID
    name: str
    email: str | None = None
    role: str | None = None
    role_template_id: uuid.UUID | None = None
    salary_expected: int | None = None
    recruiter_name: str | None = None


class CandidateUpdate(BaseModel):
    name: str | None = None
    email: str | None = None
    role: str | None = None
    role_template_id: uuid.UUID | None = None
    stage: PipelineStage | None = None
    salary_expected: int | None = None
    recruiter_name: str | None = None
    cv_url: str | None = None
    notes: str | None = None


class CandidateResponse(BaseModel):
    id: uuid.UUID
    venture_id: uuid.UUID
    name: str
    email: str | None
    role: str | None
    role_template_id: uuid.UUID | None = None
    salary_expected: int | None = None
    orientation: str | None = None
    recruiter_name: str | None = None
    cv_url: str | None = None
    stage: PipelineStage
    created_at: datetime
    updated_at: datetime
    # Populated from linked role template (not stored on candidate)
    role_salary_min: int | None = None
    role_salary_max: int | None = None
    role_salary_currency: str | None = None

    model_config = {"from_attributes": True}
