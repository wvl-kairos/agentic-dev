"""Rubric management endpoints."""

import uuid

from fastapi import APIRouter, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from talentlens.dependencies import DBSession
from talentlens.models.database.rubric import Rubric, RubricCriterion
from talentlens.schemas.rubric import RubricCreate, RubricResponse

router = APIRouter(prefix="/rubrics", tags=["rubrics"])


@router.get("/", response_model=list[RubricResponse])
async def list_rubrics(db: DBSession, venture_id: uuid.UUID | None = None):
    query = select(Rubric).options(selectinload(Rubric.criteria))
    if venture_id:
        query = query.where(Rubric.venture_id == venture_id)
    result = await db.execute(query)
    return result.scalars().all()


@router.post("/", response_model=RubricResponse, status_code=201)
async def create_rubric(data: RubricCreate, db: DBSession):
    criteria_data = data.criteria
    rubric = Rubric(**data.model_dump(exclude={"criteria"}))
    db.add(rubric)
    await db.flush()
    for c in criteria_data:
        db.add(RubricCriterion(rubric_id=rubric.id, **c.model_dump()))
    await db.commit()
    await db.refresh(rubric)
    # Reload with criteria
    result = await db.execute(
        select(Rubric).where(Rubric.id == rubric.id).options(selectinload(Rubric.criteria))
    )
    return result.scalar_one()


@router.get("/{rubric_id}", response_model=RubricResponse)
async def get_rubric(rubric_id: uuid.UUID, db: DBSession):
    result = await db.execute(
        select(Rubric).where(Rubric.id == rubric_id).options(selectinload(Rubric.criteria))
    )
    rubric = result.scalar_one_or_none()
    if not rubric:
        raise HTTPException(status_code=404, detail="Rubric not found")
    return rubric
