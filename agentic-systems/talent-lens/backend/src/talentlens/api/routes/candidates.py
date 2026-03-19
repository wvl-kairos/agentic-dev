"""Candidate CRUD endpoints."""

import uuid

from fastapi import APIRouter, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from talentlens.dependencies import DBSession
from talentlens.models.database.assessment import Assessment, CriterionScore
from talentlens.models.database.candidate import Candidate
from talentlens.schemas.candidate import CandidateCreate, CandidateResponse, CandidateUpdate

router = APIRouter(prefix="/candidates", tags=["candidates"])


@router.get("/", response_model=list[CandidateResponse])
async def list_candidates(
    db: DBSession,
    venture_id: uuid.UUID | None = None,
    stage: str | None = None,
    role_template_id: uuid.UUID | None = None,
    recruiter_name: str | None = None,
    search: str | None = None,
):
    query = select(Candidate)
    if venture_id:
        query = query.where(Candidate.venture_id == venture_id)
    if stage:
        query = query.where(Candidate.stage == stage)
    if role_template_id:
        query = query.where(Candidate.role_template_id == role_template_id)
    if recruiter_name:
        query = query.where(Candidate.recruiter_name == recruiter_name)
    if search:
        pattern = f"%{search}%"
        query = query.where(
            Candidate.name.ilike(pattern) | Candidate.email.ilike(pattern)
        )
    result = await db.execute(query.order_by(Candidate.created_at.desc()))
    return result.scalars().all()


@router.post("/", response_model=CandidateResponse, status_code=201)
async def create_candidate(data: CandidateCreate, db: DBSession):
    candidate = Candidate(**data.model_dump())
    db.add(candidate)
    await db.commit()
    await db.refresh(candidate)
    return candidate


@router.get("/{candidate_id}", response_model=CandidateResponse)
async def get_candidate(candidate_id: uuid.UUID, db: DBSession):
    candidate = await db.get(Candidate, candidate_id)
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
    # Enrich with role template salary range
    resp = CandidateResponse.model_validate(candidate)
    if candidate.role_template_id:
        from talentlens.models.database.capability import RoleTemplate
        rt = await db.get(RoleTemplate, candidate.role_template_id)
        if rt:
            resp.role_salary_min = rt.salary_min
            resp.role_salary_max = rt.salary_max
            resp.role_salary_currency = rt.salary_currency
    return resp


@router.patch("/{candidate_id}", response_model=CandidateResponse)
async def update_candidate(candidate_id: uuid.UUID, data: CandidateUpdate, db: DBSession):
    candidate = await db.get(Candidate, candidate_id)
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(candidate, field, value)
    await db.commit()
    await db.refresh(candidate)
    return candidate


@router.get("/{candidate_id}/coverage")
async def get_candidate_coverage(candidate_id: uuid.UUID, db: DBSession):
    """Aggregate criterion scores across all assessments for coverage tracking."""
    candidate = await db.get(Candidate, candidate_id)
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")

    result = await db.execute(
        select(Assessment)
        .where(Assessment.candidate_id == candidate_id)
        .options(selectinload(Assessment.criterion_scores))
        .order_by(Assessment.created_at)
    )
    assessments = result.scalars().all()

    # Build per-criterion aggregation: keep best score and track which stages assessed it
    criteria_map: dict[str, dict] = {}
    for assessment in assessments:
        for cs in assessment.criterion_scores:
            name = cs.criterion_name
            if name not in criteria_map:
                criteria_map[name] = {
                    "criterion_name": name,
                    "status": cs.assessment_status,
                    "best_score": cs.score if cs.assessment_status != "not_assessed" else None,
                    "max_score": cs.max_score,
                    "confidence_level": cs.confidence_level if cs.assessment_status != "not_assessed" else None,
                    "stages": [],
                }

            entry = criteria_map[name]

            # Upgrade status: not_assessed < assessed_negative < assessed_positive
            status_rank = {"not_assessed": 0, "assessed_negative": 1, "assessed_positive": 2}
            if status_rank.get(cs.assessment_status, 0) > status_rank.get(entry["status"], 0):
                entry["status"] = cs.assessment_status

            # Track best score (only from assessed criteria)
            if cs.assessment_status != "not_assessed":
                if entry["best_score"] is None or cs.score > entry["best_score"]:
                    entry["best_score"] = cs.score
                    entry["confidence_level"] = cs.confidence_level
                if assessment.stage not in entry["stages"]:
                    entry["stages"].append(assessment.stage)

    criteria_list = list(criteria_map.values())
    assessed_count = len([c for c in criteria_list if c["status"] != "not_assessed"])
    total_required = len(criteria_list)

    return {
        "assessed_count": assessed_count,
        "total_required": total_required,
        "coverage_ratio": round(assessed_count / total_required, 2) if total_required > 0 else 1.0,
        "criteria": criteria_list,
    }
