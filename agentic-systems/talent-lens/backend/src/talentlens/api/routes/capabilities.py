"""Capability and Role Template endpoints for skills matrix."""

import uuid

from fastapi import APIRouter, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from talentlens.dependencies import DBSession
from talentlens.models.database.capability import (
    Capability,
    RoleCapabilityRequirement,
    RoleTemplate,
    RoleTechnologyRequirement,
    Technology,
)
from talentlens.schemas.capability import (
    CapabilityResponse,
    CandidateCapabilityScore,
    CandidateSkillsResponse,
    JobDescriptionResponse,
    RoleTemplateCreate,
    RoleTemplateResponse,
    RoleTemplateUpdate,
    TechnologyResponse,
)
from talentlens.services.job_description import generate_job_description
from talentlens.models.database.candidate import Candidate
from talentlens.models.database.assessment import Assessment, CriterionScore
from talentlens.models.database.rubric import RubricCriterion

router = APIRouter(tags=["capabilities"])


# ---------------------------------------------------------------------------
# Helper: eager-load options for RoleTemplate queries
# ---------------------------------------------------------------------------

def _role_template_load_options():
    cap_load = selectinload(RoleTemplate.requirements).selectinload(
        RoleCapabilityRequirement.capability
    )
    return [
        cap_load.selectinload(Capability.levels),
        cap_load.selectinload(Capability.technologies),
        selectinload(RoleTemplate.technology_requirements)
        .selectinload(RoleTechnologyRequirement.technology),
    ]


# ---------------------------------------------------------------------------
# Capabilities (read-only — seeded via migration)
# ---------------------------------------------------------------------------


@router.get("/capabilities/", response_model=list[CapabilityResponse])
async def list_capabilities(db: DBSession):
    """List all engineering capabilities with levels and technologies."""
    result = await db.execute(
        select(Capability)
        .options(
            selectinload(Capability.levels),
            selectinload(Capability.technologies),
        )
        .order_by(Capability.order)
    )
    return result.scalars().all()


@router.get("/capabilities/{capability_id}", response_model=CapabilityResponse)
async def get_capability(capability_id: uuid.UUID, db: DBSession):
    result = await db.execute(
        select(Capability)
        .where(Capability.id == capability_id)
        .options(
            selectinload(Capability.levels),
            selectinload(Capability.technologies),
        )
    )
    cap = result.scalar_one_or_none()
    if not cap:
        raise HTTPException(status_code=404, detail="Capability not found")
    return cap


# ---------------------------------------------------------------------------
# Technologies (read-only — seeded via migration)
# ---------------------------------------------------------------------------


@router.get("/technologies/", response_model=list[TechnologyResponse])
async def list_technologies(db: DBSession, capability_id: uuid.UUID | None = None):
    """List all technologies, optionally filtered by capability."""
    query = select(Technology).order_by(Technology.order)
    if capability_id:
        query = query.where(Technology.capability_id == capability_id)
    result = await db.execute(query)
    return result.scalars().all()


# ---------------------------------------------------------------------------
# Role Templates
# ---------------------------------------------------------------------------


@router.get("/role-templates/", response_model=list[RoleTemplateResponse])
async def list_role_templates(db: DBSession, venture_id: uuid.UUID | None = None):
    query = select(RoleTemplate).options(*_role_template_load_options())
    if venture_id:
        query = query.where(RoleTemplate.venture_id == venture_id)
    result = await db.execute(query.order_by(RoleTemplate.created_at.desc()))
    return result.scalars().all()


@router.post("/role-templates/", response_model=RoleTemplateResponse, status_code=201)
async def create_role_template(data: RoleTemplateCreate, db: DBSession):
    template = RoleTemplate(
        venture_id=data.venture_id,
        name=data.name,
        description=data.description,
    )
    db.add(template)
    await db.flush()

    for req in data.requirements:
        db.add(RoleCapabilityRequirement(
            role_template_id=template.id,
            capability_id=req.capability_id,
            required_level=req.required_level,
        ))

    for treq in data.technology_requirements:
        db.add(RoleTechnologyRequirement(
            role_template_id=template.id,
            technology_id=treq.technology_id,
            required_level=treq.required_level,
        ))

    await db.commit()

    result = await db.execute(
        select(RoleTemplate)
        .where(RoleTemplate.id == template.id)
        .options(*_role_template_load_options())
    )
    return result.scalar_one()


@router.get("/role-templates/{template_id}", response_model=RoleTemplateResponse)
async def get_role_template(template_id: uuid.UUID, db: DBSession):
    result = await db.execute(
        select(RoleTemplate)
        .where(RoleTemplate.id == template_id)
        .options(*_role_template_load_options())
    )
    template = result.scalar_one_or_none()
    if not template:
        raise HTTPException(status_code=404, detail="Role template not found")
    return template


@router.put("/role-templates/{template_id}", response_model=RoleTemplateResponse)
async def update_role_template(
    template_id: uuid.UUID, data: RoleTemplateUpdate, db: DBSession
):
    result = await db.execute(
        select(RoleTemplate).where(RoleTemplate.id == template_id)
    )
    template = result.scalar_one_or_none()
    if not template:
        raise HTTPException(status_code=404, detail="Role template not found")

    if data.name is not None:
        template.name = data.name
    if data.description is not None:
        template.description = data.description

    # Replace capability requirements if provided
    if data.requirements is not None:
        existing = await db.execute(
            select(RoleCapabilityRequirement).where(
                RoleCapabilityRequirement.role_template_id == template_id
            )
        )
        for req in existing.scalars().all():
            await db.delete(req)
        for req in data.requirements:
            db.add(RoleCapabilityRequirement(
                role_template_id=template_id,
                capability_id=req.capability_id,
                required_level=req.required_level,
            ))

    # Replace technology requirements if provided
    if data.technology_requirements is not None:
        existing = await db.execute(
            select(RoleTechnologyRequirement).where(
                RoleTechnologyRequirement.role_template_id == template_id
            )
        )
        for treq in existing.scalars().all():
            await db.delete(treq)
        for treq in data.technology_requirements:
            db.add(RoleTechnologyRequirement(
                role_template_id=template_id,
                technology_id=treq.technology_id,
                required_level=treq.required_level,
            ))

    await db.commit()

    result = await db.execute(
        select(RoleTemplate)
        .where(RoleTemplate.id == template_id)
        .options(*_role_template_load_options())
    )
    return result.scalar_one()


@router.delete("/role-templates/{template_id}", status_code=204)
async def delete_role_template(template_id: uuid.UUID, db: DBSession):
    result = await db.execute(
        select(RoleTemplate).where(RoleTemplate.id == template_id)
    )
    template = result.scalar_one_or_none()
    if not template:
        raise HTTPException(status_code=404, detail="Role template not found")
    await db.delete(template)
    await db.commit()


# ---------------------------------------------------------------------------
# Job Description Generation
# ---------------------------------------------------------------------------


@router.post(
    "/role-templates/{template_id}/generate-jd",
    response_model=JobDescriptionResponse,
)
async def generate_jd_from_template(template_id: uuid.UUID, db: DBSession):
    """Generate a job description from a role template using Claude."""
    result = await db.execute(
        select(RoleTemplate)
        .where(RoleTemplate.id == template_id)
        .options(*_role_template_load_options())
    )
    template = result.scalar_one_or_none()
    if not template:
        raise HTTPException(status_code=404, detail="Role template not found")

    # Build capability data for the generator
    capabilities = []
    for req in template.requirements:
        cap = req.capability
        capabilities.append({
            "name": cap.name if cap else "Unknown",
            "description": cap.description if cap else None,
            "required_level": req.required_level,
        })

    # Build technology data for the generator
    technologies = []
    for treq in template.technology_requirements:
        tech = treq.technology
        # Find parent capability name
        cap_name = ""
        if tech:
            for req in template.requirements:
                if req.capability and req.capability.id == tech.capability_id:
                    cap_name = req.capability.name
                    break
            if not cap_name:
                # Look up capability directly
                cap_result = await db.execute(
                    select(Capability).where(Capability.id == tech.capability_id)
                )
                parent_cap = cap_result.scalar_one_or_none()
                cap_name = parent_cap.name if parent_cap else ""

        technologies.append({
            "name": tech.name if tech else "Unknown",
            "capability_name": cap_name,
            "required_level": treq.required_level,
        })

    jd = await generate_job_description(
        name=template.name,
        description=template.description,
        capabilities=capabilities,
        technologies=technologies,
    )
    return jd


# ---------------------------------------------------------------------------
# Candidate Skills View
# ---------------------------------------------------------------------------


@router.get("/candidates/{candidate_id}/skills", response_model=CandidateSkillsResponse)
async def get_candidate_skills(candidate_id: uuid.UUID, db: DBSession):
    """Get aggregated capability scores for a candidate across all assessments."""
    candidate = await db.get(Candidate, candidate_id)
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")

    # Load role template requirements if assigned
    role_template = None
    required_levels: dict[uuid.UUID, int] = {}
    if candidate.role_template_id:
        rt_result = await db.execute(
            select(RoleTemplate)
            .where(RoleTemplate.id == candidate.role_template_id)
            .options(*_role_template_load_options())
        )
        role_template = rt_result.scalar_one_or_none()
        if role_template:
            for req in role_template.requirements:
                required_levels[req.capability_id] = req.required_level

    # Get all capabilities
    cap_result = await db.execute(
        select(Capability)
        .options(selectinload(Capability.levels), selectinload(Capability.technologies))
        .order_by(Capability.order)
    )
    capabilities = cap_result.scalars().all()

    # Get all assessments for this candidate with criterion scores
    assess_result = await db.execute(
        select(Assessment)
        .where(Assessment.candidate_id == candidate_id)
        .options(selectinload(Assessment.criterion_scores))
    )
    assessments = assess_result.scalars().all()

    # Link criterion names to capabilities via rubric_criteria
    criterion_names: set[str] = set()
    for a in assessments:
        for cs in a.criterion_scores:
            criterion_names.add(cs.criterion_name)

    cap_map: dict[str, uuid.UUID] = {}
    if criterion_names:
        rc_result = await db.execute(
            select(RubricCriterion)
            .where(
                RubricCriterion.name.in_(criterion_names),
                RubricCriterion.capability_id.isnot(None),
            )
        )
        for rc in rc_result.scalars().all():
            if rc.capability_id:
                cap_map[rc.name] = rc.capability_id

    # Aggregate scores by capability
    cap_scores: dict[uuid.UUID, list[tuple[int, int]]] = {}
    for a in assessments:
        for cs in a.criterion_scores:
            cap_id = cap_map.get(cs.criterion_name)
            if cap_id:
                cap_scores.setdefault(cap_id, []).append((cs.score, cs.max_score))

    capability_scores = []
    for cap in capabilities:
        scores = cap_scores.get(cap.id, [])
        if scores:
            avg = sum(s for s, _ in scores) / len(scores)
            max_s = max(m for _, m in scores)
            count = len(scores)
        else:
            avg = None
            max_s = 5.0
            count = 0

        capability_scores.append(CandidateCapabilityScore(
            capability_id=cap.id,
            capability_name=cap.name,
            capability_slug=cap.slug,
            required_level=required_levels.get(cap.id),
            avg_score=round(avg, 2) if avg is not None else None,
            max_score=max_s,
            assessment_count=count,
        ))

    return CandidateSkillsResponse(
        candidate_id=candidate.id,
        candidate_name=candidate.name,
        role_template=role_template,
        capabilities=capability_scores,
    )
