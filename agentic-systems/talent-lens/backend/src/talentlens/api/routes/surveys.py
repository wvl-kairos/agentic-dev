"""In-platform capabilities survey endpoints."""

import math
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from talentlens.dependencies import DBSession
from talentlens.models.database.capability import (
    Capability,
    RoleCapabilityRequirement,
    RoleTemplate,
)
from talentlens.models.database.survey import SurveyAnswer, SurveyResponse
from talentlens.schemas.survey import (
    SurveyAggregateScore,
    SurveyCreate,
    SurveyResponseResponse,
)

router = APIRouter(prefix="/surveys", tags=["surveys"])


@router.post("/role-template/{role_template_id}", response_model=SurveyResponseResponse, status_code=201)
async def create_survey_response(
    role_template_id: uuid.UUID, data: SurveyCreate, db: DBSession
):
    """Submit a survey response for a role template."""
    template = await db.get(RoleTemplate, role_template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Role template not found")

    response = SurveyResponse(
        role_template_id=role_template_id,
        respondent_name=data.respondent_name,
        respondent_email=data.respondent_email,
        completed_at=datetime.now(timezone.utc),
    )
    db.add(response)
    await db.flush()

    for answer in data.answers:
        if answer.score < 1 or answer.score > 10:
            raise HTTPException(status_code=422, detail=f"Score must be 1-10, got {answer.score}")
        db.add(SurveyAnswer(
            survey_response_id=response.id,
            capability_id=answer.capability_id,
            score=answer.score,
        ))

    await db.commit()

    # Re-fetch with answers loaded
    result = await db.execute(
        select(SurveyResponse)
        .where(SurveyResponse.id == response.id)
        .options(selectinload(SurveyResponse.answers))
    )
    return result.scalar_one()


@router.get("/role-template/{role_template_id}", response_model=list[SurveyResponseResponse])
async def list_survey_responses(role_template_id: uuid.UUID, db: DBSession):
    """List all survey responses for a role template."""
    result = await db.execute(
        select(SurveyResponse)
        .where(SurveyResponse.role_template_id == role_template_id)
        .options(selectinload(SurveyResponse.answers))
        .order_by(SurveyResponse.created_at.desc())
    )
    return result.scalars().all()


@router.get("/role-template/{role_template_id}/aggregate", response_model=list[SurveyAggregateScore])
async def get_aggregate_scores(role_template_id: uuid.UUID, db: DBSession):
    """Get averaged survey scores per capability for a role template."""
    template = await db.get(RoleTemplate, role_template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Role template not found")

    # Aggregate scores by capability
    result = await db.execute(
        select(
            SurveyAnswer.capability_id,
            func.avg(SurveyAnswer.score).label("avg_score"),
            func.count(SurveyAnswer.id).label("response_count"),
        )
        .join(SurveyResponse, SurveyAnswer.survey_response_id == SurveyResponse.id)
        .where(SurveyResponse.role_template_id == role_template_id)
        .group_by(SurveyAnswer.capability_id)
    )
    rows = result.all()

    # Fetch capability names
    cap_ids = [r[0] for r in rows]
    if not cap_ids:
        return []

    caps_result = await db.execute(
        select(Capability).where(Capability.id.in_(cap_ids))
    )
    cap_map = {c.id: c.name for c in caps_result.scalars().all()}

    return [
        SurveyAggregateScore(
            capability_id=row[0],
            capability_name=cap_map.get(row[0], "Unknown"),
            avg_score=round(float(row[1]), 1),
            response_count=int(row[2]),
        )
        for row in rows
    ]


@router.post("/role-template/{role_template_id}/apply")
async def apply_survey_results(role_template_id: uuid.UUID, db: DBSession):
    """Write aggregated survey scores to role_capability_requirements.survey_level."""
    template = await db.get(RoleTemplate, role_template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Role template not found")

    # Get aggregated scores
    result = await db.execute(
        select(
            SurveyAnswer.capability_id,
            func.avg(SurveyAnswer.score).label("avg_score"),
        )
        .join(SurveyResponse, SurveyAnswer.survey_response_id == SurveyResponse.id)
        .where(SurveyResponse.role_template_id == role_template_id)
        .group_by(SurveyAnswer.capability_id)
    )
    aggregates = {row[0]: round(float(row[1])) for row in result.all()}

    if not aggregates:
        return {"updated": 0, "message": "No survey responses to apply"}

    # Update existing requirements
    req_result = await db.execute(
        select(RoleCapabilityRequirement).where(
            RoleCapabilityRequirement.role_template_id == role_template_id
        )
    )
    requirements = req_result.scalars().all()

    updated = 0
    for req in requirements:
        if req.capability_id in aggregates:
            survey_level = aggregates[req.capability_id]
            req.survey_level = survey_level
            req.required_level = math.ceil(survey_level / 2)
            updated += 1

    await db.commit()
    return {"updated": updated, "message": f"Applied survey scores to {updated} requirements"}
