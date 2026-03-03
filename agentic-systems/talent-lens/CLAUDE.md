# TalentLens — Interview Intelligence Platform

## What is this?
AI-powered candidate evaluation platform for UP Labs. Replaces manual interview review with automated assessments using Claude API.

## Architecture
- **Backend**: FastAPI + SQLAlchemy (async) + PostgreSQL (Supabase)
- **Frontend**: React 18 + Vite + shadcn/ui + Zustand
- **Processing**: FastAPI BackgroundTasks (event-driven, no Celery)
- **Deployment**: GCP Cloud Run + Artifact Registry

## Candidate Pipeline (event-driven state machine)
```
screening → coderpad → technical_interview → final_interview → decision
```
Each stage is triggered by external events (webhooks). Each produces an Assessment. Aggregation layer combines all stages into a unified scorecard.

## Key Patterns
- Backend package: `backend/src/talentlens/`
- Config: Pydantic Settings (`config.py`)
- Models: SQLAlchemy async with UUID PKs (`models/database/`)
- Schemas: Pydantic v2 (`schemas/`)
- Routes: FastAPI routers under `api/routes/`, all prefixed with `/api`
- Services: Business logic in `services/`

## Commands
```bash
# Backend
cd backend && uv sync
uv run alembic upgrade head
uv run uvicorn talentlens.main:app --reload

# Frontend
cd frontend && npm install
npm run dev

# Full stack
docker compose up --build
```
