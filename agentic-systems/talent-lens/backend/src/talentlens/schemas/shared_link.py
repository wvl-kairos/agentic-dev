"""Schemas for shared candidate profile links."""

import uuid
from datetime import datetime

from pydantic import BaseModel


class SharedLinkCreate(BaseModel):
    candidate_id: uuid.UUID
    created_by: str | None = None
    expires_days: int | None = None  # None = no expiry


class SharedLinkResponse(BaseModel):
    id: uuid.UUID
    candidate_id: uuid.UUID
    token: str
    created_by: str | None
    expires_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}
