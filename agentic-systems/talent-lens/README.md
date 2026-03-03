# TalentLens

AI-powered interview intelligence platform for UP Labs. Automates candidate evaluation across the full hiring pipeline — from screening to final decision.

## Quick Start

### Prerequisites
- Python 3.12+ with [uv](https://docs.astral.sh/uv/)
- Node.js 20+
- Docker & Docker Compose

### Development

```bash
# Start infrastructure
docker compose up -d postgres

# Backend
cd backend
uv sync
uv run alembic upgrade head
uv run uvicorn talentlens.main:app --reload  # → localhost:8000

# Frontend (separate terminal)
cd frontend
npm install
npm run dev  # → localhost:5173
```

### Docker (full stack)

```bash
docker compose up --build
# Frontend → localhost:3000
# Backend  → localhost:8000
# API docs → localhost:8000/docs
```

## Architecture

```
Fireflies webhook → Transcript ingestion → Talk ratio + Contribution detection
    → Claude assessment → Scorecard → Slack notification
```

Each candidate moves through pipeline stages (`screening → coderpad → technical → final → decision`), accumulating assessments at each step. Venture leads get a unified scorecard with evidence-backed scores.
