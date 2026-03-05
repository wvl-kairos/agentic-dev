import uuid
from datetime import datetime

from pydantic import BaseModel


class RubricCriterionCreate(BaseModel):
    name: str
    description: str | None = None
    capability_id: uuid.UUID | None = None
    weight: float = 1.0
    max_score: int = 5
    order: int = 0


class RubricCreate(BaseModel):
    venture_id: uuid.UUID
    name: str
    role: str | None = None
    description: str | None = None
    criteria: list[RubricCriterionCreate] = []


class RubricCriterionResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: str | None
    capability_id: uuid.UUID | None = None
    weight: float
    max_score: int
    order: int

    model_config = {"from_attributes": True}


class RubricResponse(BaseModel):
    id: uuid.UUID
    venture_id: uuid.UUID
    name: str
    role: str | None
    description: str | None
    criteria: list[RubricCriterionResponse] = []
    created_at: datetime

    model_config = {"from_attributes": True}
