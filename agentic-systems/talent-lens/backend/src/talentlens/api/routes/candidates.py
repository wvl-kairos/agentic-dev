"""Candidate CRUD endpoints."""

import uuid

from fastapi import APIRouter, HTTPException
from sqlalchemy import select

from talentlens.dependencies import DBSession
from talentlens.models.database.candidate import Candidate
from talentlens.schemas.candidate import CandidateCreate, CandidateResponse, CandidateUpdate

router = APIRouter(prefix="/candidates", tags=["candidates"])


@router.get("/", response_model=list[CandidateResponse])
async def list_candidates(db: DBSession, venture_id: uuid.UUID | None = None):
    query = select(Candidate)
    if venture_id:
        query = query.where(Candidate.venture_id == venture_id)
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
    return candidate


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
