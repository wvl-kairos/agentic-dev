"""Assessment result endpoints."""

import uuid

from fastapi import APIRouter, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from talentlens.dependencies import DBSession
from talentlens.models.database.assessment import Assessment, CriterionScore
from talentlens.schemas.assessment import AssessmentResponse

router = APIRouter(prefix="/assessments", tags=["assessments"])


@router.get("/candidate/{candidate_id}", response_model=list[AssessmentResponse])
async def list_candidate_assessments(candidate_id: uuid.UUID, db: DBSession):
    """Get all assessments for a candidate across pipeline stages."""
    result = await db.execute(
        select(Assessment)
        .where(Assessment.candidate_id == candidate_id)
        .options(
            selectinload(Assessment.criterion_scores).selectinload(CriterionScore.evidence)
        )
        .order_by(Assessment.created_at)
    )
    return result.scalars().all()


@router.get("/{assessment_id}", response_model=AssessmentResponse)
async def get_assessment(assessment_id: uuid.UUID, db: DBSession):
    result = await db.execute(
        select(Assessment)
        .where(Assessment.id == assessment_id)
        .options(
            selectinload(Assessment.criterion_scores).selectinload(CriterionScore.evidence)
        )
    )
    assessment = result.scalar_one_or_none()
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")
    return assessment
