"""Shared candidate profile link endpoints."""

import secrets
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from talentlens.dependencies import DBSession
from talentlens.models.database.shared_link import SharedLink
from talentlens.models.database.candidate import Candidate
from talentlens.models.database.assessment import Assessment
from talentlens.schemas.shared_link import SharedLinkCreate, SharedLinkResponse

router = APIRouter(prefix="/shared-links", tags=["shared-links"])


@router.post("/", response_model=SharedLinkResponse, status_code=201)
async def create_shared_link(data: SharedLinkCreate, db: DBSession):
    """Create a shareable link for a candidate profile."""
    candidate = await db.get(Candidate, data.candidate_id)
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")

    token = secrets.token_urlsafe(32)
    expires_at = None
    if data.expires_days:
        expires_at = datetime.now(timezone.utc) + timedelta(days=data.expires_days)

    link = SharedLink(
        candidate_id=data.candidate_id,
        token=token,
        created_by=data.created_by,
        expires_at=expires_at,
    )
    db.add(link)
    await db.commit()
    await db.refresh(link)
    return link


@router.get("/public/{token}")
async def get_public_candidate(token: str, db: DBSession):
    """Public endpoint — returns candidate + assessments by token. No auth required."""
    result = await db.execute(
        select(SharedLink).where(SharedLink.token == token)
    )
    link = result.scalar_one_or_none()
    if not link:
        raise HTTPException(status_code=404, detail="Link not found")

    # Check expiry
    if link.expires_at and link.expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=410, detail="Link has expired")

    candidate = await db.get(Candidate, link.candidate_id)
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")

    # Get assessments
    assess_result = await db.execute(
        select(Assessment)
        .where(Assessment.candidate_id == candidate.id)
        .options(selectinload(Assessment.criterion_scores))
        .order_by(Assessment.created_at)
    )
    assessments = assess_result.scalars().all()

    return {
        "candidate": {
            "id": str(candidate.id),
            "name": candidate.name,
            "role": candidate.role,
            "stage": candidate.stage.value,
            "email": candidate.email,
            "cv_url": candidate.cv_url,
        },
        "assessments": [
            {
                "id": str(a.id),
                "stage": a.stage,
                "overall_score": a.overall_score,
                "summary": a.summary,
                "recommendation": a.recommendation,
                "criterion_scores": [
                    {
                        "criterion_name": cs.criterion_name,
                        "score": cs.score,
                        "max_score": cs.max_score,
                        "confidence_level": cs.confidence_level,
                        "assessment_status": cs.assessment_status,
                    }
                    for cs in a.criterion_scores
                ],
                "created_at": a.created_at.isoformat(),
            }
            for a in assessments
        ],
    }


@router.get("/candidate/{candidate_id}", response_model=list[SharedLinkResponse])
async def list_candidate_links(candidate_id: uuid.UUID, db: DBSession):
    """List all shared links for a candidate."""
    result = await db.execute(
        select(SharedLink)
        .where(SharedLink.candidate_id == candidate_id)
        .order_by(SharedLink.created_at.desc())
    )
    return result.scalars().all()
