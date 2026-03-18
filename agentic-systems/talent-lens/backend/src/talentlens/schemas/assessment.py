import uuid
from datetime import datetime

from pydantic import BaseModel


class EvidenceResponse(BaseModel):
    quote: str
    speaker: str | None
    relevance: str | None

    model_config = {"from_attributes": True}


class CriterionScoreResponse(BaseModel):
    criterion_name: str
    score: int
    max_score: int
    confidence_level: str = "demonstrated"
    assessment_status: str = "assessed_positive"
    reasoning: str | None
    evidence: list[EvidenceResponse] = []

    model_config = {"from_attributes": True}


class AssessmentResponse(BaseModel):
    id: uuid.UUID
    candidate_id: uuid.UUID
    interview_id: uuid.UUID | None
    stage: str
    overall_score: float | None
    summary: str | None
    recommendation: str | None
    criterion_scores: list[CriterionScoreResponse] = []
    created_at: datetime

    model_config = {"from_attributes": True}
