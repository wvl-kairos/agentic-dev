"""Venture CRUD endpoints."""

import uuid

from fastapi import APIRouter, HTTPException
from sqlalchemy import select

from talentlens.dependencies import DBSession
from talentlens.models.database.venture import Venture
from talentlens.schemas.venture import VentureCreate, VentureResponse

router = APIRouter(prefix="/ventures", tags=["ventures"])


@router.get("/", response_model=list[VentureResponse])
async def list_ventures(db: DBSession):
    result = await db.execute(select(Venture).order_by(Venture.created_at.desc()))
    return result.scalars().all()


@router.post("/", response_model=VentureResponse, status_code=201)
async def create_venture(data: VentureCreate, db: DBSession):
    venture = Venture(**data.model_dump())
    db.add(venture)
    await db.commit()
    await db.refresh(venture)
    return venture


@router.get("/{venture_id}", response_model=VentureResponse)
async def get_venture(venture_id: uuid.UUID, db: DBSession):
    venture = await db.get(Venture, venture_id)
    if not venture:
        raise HTTPException(status_code=404, detail="Venture not found")
    return venture
