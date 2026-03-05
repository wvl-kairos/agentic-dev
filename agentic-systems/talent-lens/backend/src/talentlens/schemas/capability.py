"""Schemas for capabilities, role templates, and skills tracking."""

import uuid
from datetime import datetime

from pydantic import BaseModel


# ---------------------------------------------------------------------------
# Technology
# ---------------------------------------------------------------------------

class TechnologyResponse(BaseModel):
    id: uuid.UUID
    name: str
    slug: str
    icon: str | None
    capability_id: uuid.UUID
    order: int

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Capability
# ---------------------------------------------------------------------------

class CapabilityLevelResponse(BaseModel):
    id: uuid.UUID
    level: int
    title: str
    description: str | None

    model_config = {"from_attributes": True}


class CapabilityResponse(BaseModel):
    id: uuid.UUID
    name: str
    slug: str
    description: str | None
    icon: str | None
    order: int
    levels: list[CapabilityLevelResponse] = []
    technologies: list[TechnologyResponse] = []

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Role Template
# ---------------------------------------------------------------------------

class RoleCapabilityRequirementCreate(BaseModel):
    capability_id: uuid.UUID
    required_level: int  # 1-5


class RoleTechnologyRequirementCreate(BaseModel):
    technology_id: uuid.UUID
    required_level: int  # 1-5


class RoleTemplateCreate(BaseModel):
    venture_id: uuid.UUID
    name: str
    description: str | None = None
    requirements: list[RoleCapabilityRequirementCreate] = []
    technology_requirements: list[RoleTechnologyRequirementCreate] = []


class RoleTemplateUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    requirements: list[RoleCapabilityRequirementCreate] | None = None
    technology_requirements: list[RoleTechnologyRequirementCreate] | None = None


class RoleCapabilityRequirementResponse(BaseModel):
    id: uuid.UUID
    capability_id: uuid.UUID
    capability: CapabilityResponse | None = None
    required_level: int

    model_config = {"from_attributes": True}


class RoleTechnologyRequirementResponse(BaseModel):
    id: uuid.UUID
    technology_id: uuid.UUID
    technology: TechnologyResponse | None = None
    required_level: int

    model_config = {"from_attributes": True}


class RoleTemplateResponse(BaseModel):
    id: uuid.UUID
    venture_id: uuid.UUID
    name: str
    description: str | None
    requirements: list[RoleCapabilityRequirementResponse] = []
    technology_requirements: list[RoleTechnologyRequirementResponse] = []
    created_at: datetime

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Candidate Skills View
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Job Description
# ---------------------------------------------------------------------------

class JobDescriptionResponse(BaseModel):
    """Generated job description from a role template."""
    title: str
    summary: str
    about_role: str
    responsibilities: list[str] = []
    required_qualifications: list[str] = []
    preferred_qualifications: list[str] = []
    tech_stack: list[str] = []
    level: str


# ---------------------------------------------------------------------------
# Candidate Skills View
# ---------------------------------------------------------------------------

class CandidateCapabilityScore(BaseModel):
    """Aggregated score for a single capability across all assessments."""
    capability_id: uuid.UUID
    capability_name: str
    capability_slug: str
    required_level: int | None  # from role template, null if no template
    avg_score: float | None  # averaged from assessment criterion scores
    max_score: float
    assessment_count: int  # how many assessments contributed


class CandidateSkillsResponse(BaseModel):
    """Full skills matrix for a candidate."""
    candidate_id: uuid.UUID
    candidate_name: str
    role_template: RoleTemplateResponse | None
    capabilities: list[CandidateCapabilityScore]
