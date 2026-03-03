import uuid
from datetime import datetime

from pydantic import BaseModel


class VentureCreate(BaseModel):
    name: str
    slug: str
    description: str | None = None


class VentureResponse(BaseModel):
    id: uuid.UUID
    name: str
    slug: str
    description: str | None
    created_at: datetime

    model_config = {"from_attributes": True}
