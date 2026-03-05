# TalentLens

AI-powered interview intelligence platform for [UP Labs](https://uplabs.co). Automates end-to-end candidate evaluation across the full hiring pipeline — from Fireflies transcript ingestion through Claude-powered assessment to Slack-delivered scorecards.

Built for venture studios hiring technical talent at scale, where every interview needs consistent, evidence-backed evaluation aligned to role-specific skills.

## Features

### Interview Pipeline (Event-Driven State Machine)

```
screening → coderpad → technical_interview → final_interview → decision → hired / rejected
```

- **Fireflies.ai Webhook Integration** — Receives meeting transcripts automatically via authenticated webhooks (HMAC-SHA256 signature validation)
- **Transcript Ingestion** — Parses speaker-labeled diarization segments, stores full transcripts with speaker attribution
- **Talk Ratio Analysis** — Computes candidate vs. interviewer speaking time from diarization data; uses speaker identification heuristics (name matching + duration-based fallback)
- **Contribution Detection** — Identifies individual ownership ("I built", "my solution") vs. collective language ("we built", "our team") with bilingual support (English + Spanish) and cultural sensitivity for LATAM candidates
- **Claude AI Assessment** — Scores interviews against rubric criteria using Claude API with structured JSON output; every score backed by exact transcript quotes
- **Anti-Hallucination Validation** — Evidence quotes are verified as exact substrings of the transcript; hallucinated quotes are stripped from results
- **Automatic Stage Advancement** — Candidates progress through pipeline stages after each assessment (unless rejected)
- **Slack Notifications** — Real-time alerts when assessments complete, with score, recommendation, and scorecard link

### Skills Matrix Framework

Two-level hierarchy for defining and tracking engineering competencies:

**7 Engineering Capabilities** — Frontend, Backend, Data Engineering, Data Science & ML, Analytics & Insights, DevOps & Infrastructure, Leadership — each with 5 proficiency levels (Junior → Expert)

**~80 Technology Stacks** — Specific technologies grouped under capabilities (React, Python, Kubernetes, TensorFlow, etc.), each with independent proficiency tracking

- **Role Templates** — Define required capability levels and technology proficiencies for any engineering position
- **Candidate Skills View** — Aggregated capability scores across all assessments, compared against role template requirements for gap analysis
- **Drag-and-Drop Technology Selection** — Interactive palette with grouped, searchable technologies; drag or click to add to role templates

### Job Description Generation

- **AI-Powered JD Creation** — Generates structured, professional job descriptions from role templates using Claude API
- **Template-Driven** — Automatically incorporates capability requirements, technology stack, and proficiency levels
- **Editable Output** — Generated JDs can be copied, customized, and used across job boards

### Assessment Scorecards

- **Per-Stage Assessments** — Individual scorecards for each pipeline stage (screening, coderpad, technical, final)
- **Criterion Scores with Evidence** — Each rubric criterion scored 0-5 with reasoning and transcript quotes
- **Recommendations** — Six-level scale: strong_yes, yes, lean_yes, lean_no, no, strong_no
- **Talk Ratio Visualization** — Bar chart showing candidate vs interviewer speaking time
- **Skills Radar** — Bar chart visualization of candidate capabilities vs. role requirements

### Role-Template-Aware Evaluation

The assessment engine dynamically builds evaluation criteria from the candidate's assigned role template:

- **Capability-Based Criteria** — Each required capability becomes a scoring criterion with context-appropriate descriptions and weighted by required level
- **Technology-Specific Criteria** — Required technologies are evaluated for depth of knowledge, practical experience, and proficiency
- **Contextual Scoring Prompt** — Claude receives the full role context (title, description, required skills) when evaluating transcripts, producing assessments aligned to what the role actually needs
- **Fallback to Manual Rubrics** — If no role template is assigned, the engine falls back to venture-level rubrics or sensible defaults

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         TalentLens                                  │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  Fireflies.ai ──webhook──→ Ingestion ──→ Interview Record          │
│                              │                                      │
│                              ▼                                      │
│                     ┌─ BackgroundTask ─┐                            │
│                     │  1. Talk Ratio   │                            │
│                     │  2. Contribution │                            │
│                     │  3. Rubric Match │◄── Role Template / Rubric  │
│                     │  4. Claude Score │                            │
│                     │  5. Persist      │                            │
│                     │  6. Stage Adv.   │                            │
│                     │  7. Slack Notify │                            │
│                     └──────────────────┘                            │
│                              │                                      │
│                              ▼                                      │
│               Assessment + CriterionScores + Evidence               │
│                              │                                      │
│                              ▼                                      │
│                    React Dashboard + Scorecards                     │
│                                                                     │
├─────────────────────────────────────────────────────────────────────┤
│  Role Templates ──→ Job Description (Claude) ──→ JD Output         │
│  Role Templates ──→ Dynamic Rubric Criteria ──→ Scoring Engine     │
└─────────────────────────────────────────────────────────────────────┘
```

### Tech Stack

| Layer | Technology |
|---|---|
| **Backend** | Python 3.12, FastAPI, SQLAlchemy 2.0 (async), Pydantic v2 |
| **Database** | PostgreSQL (Supabase), Alembic migrations |
| **AI** | Claude API (Anthropic) — assessment scoring + JD generation |
| **Transcription** | Fireflies.ai (webhook), Deepgram (planned) |
| **Frontend** | React 18, Vite, TypeScript, Tailwind CSS, shadcn/ui |
| **Drag & Drop** | @dnd-kit (core + sortable + utilities) |
| **Notifications** | Slack Bot API |
| **Deployment** | GCP Cloud Run, Artifact Registry, Cloud Build |
| **Background Tasks** | FastAPI BackgroundTasks (event-driven, no Celery/Redis) |

## API Endpoints

### Core Resources

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/health` | Health check with database status |
| `GET/POST` | `/api/ventures/` | List / create ventures |
| `GET` | `/api/ventures/{id}` | Get venture details |
| `GET/POST` | `/api/candidates/` | List / create candidates |
| `GET/PATCH` | `/api/candidates/{id}` | Get / update candidate |
| `POST` | `/api/interviews/` | Create interview (triggers assessment pipeline) |
| `GET` | `/api/interviews/candidate/{id}` | List candidate interviews |
| `GET` | `/api/interviews/{id}` | Get interview details |
| `GET` | `/api/assessments/candidate/{id}` | List candidate assessments with scores + evidence |
| `GET` | `/api/assessments/{id}` | Get assessment details |
| `GET/POST` | `/api/rubrics/` | List / create evaluation rubrics |
| `GET` | `/api/rubrics/{id}` | Get rubric with criteria |
| `GET` | `/api/dashboard/metrics` | Pipeline metrics and stage counts |

### Skills Matrix

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/capabilities/` | List all capabilities with levels and technologies |
| `GET` | `/api/capabilities/{id}` | Get capability details |
| `GET` | `/api/technologies/` | List technologies (optional `?capability_id` filter) |
| `GET/POST` | `/api/role-templates/` | List / create role templates |
| `GET/PUT/DELETE` | `/api/role-templates/{id}` | Get / update / delete role template |
| `POST` | `/api/role-templates/{id}/generate-jd` | Generate job description from template |
| `GET` | `/api/candidates/{id}/skills` | Aggregated capability scores vs. role requirements |

### Webhooks

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/webhooks/fireflies` | Fireflies.ai transcript webhook (HMAC-SHA256) |
| `POST` | `/api/webhooks/coderpad` | CoderPad challenge results (planned) |

## Database Schema

14 tables across 4 domains:

**Ventures & Candidates** — `ventures`, `candidates` (with pipeline stage enum and role template assignment)

**Interviews & Assessments** — `interviews` (transcript, diarization, talk ratio), `assessments` (overall score, recommendation, summary), `criterion_scores` (per-criterion with reasoning), `evidence` (exact transcript quotes with speaker attribution)

**Rubrics** — `rubrics` (venture-scoped), `rubric_criteria` (weighted criteria linked to capabilities)

**Skills Matrix** — `capabilities` (7 engineering areas), `capability_levels` (proficiency 1-5), `technologies` (~80 stacks), `role_templates`, `role_capability_requirements`, `role_technology_requirements`

## Getting Started

### Prerequisites

- Python 3.12+ with [uv](https://docs.astral.sh/uv/)
- Node.js 20+
- Docker & Docker Compose
- PostgreSQL (or Supabase project)

### Environment Variables

```bash
cp .env.example .env
# Edit .env with your credentials:
#   DATABASE_URL          — PostgreSQL connection string
#   ANTHROPIC_API_KEY     — Claude API key
#   FIREFLIES_API_KEY     — Fireflies.ai API key
#   FIREFLIES_WEBHOOK_SECRET — HMAC secret for webhook validation
#   SLACK_BOT_TOKEN       — Slack Bot OAuth token
#   SLACK_DEFAULT_CHANNEL — Slack channel for notifications
```

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

### Docker (Full Stack)

```bash
docker compose up --build
# Frontend → localhost:3000
# Backend  → localhost:8000
# API docs → localhost:8000/docs
```

### Deployment (GCP Cloud Run)

```bash
./deploy.sh
# Uses Cloud Build → Artifact Registry → Cloud Run
```

## Project Structure

```
talent-lens/
├── backend/
│   ├── alembic/versions/         # Database migrations with seed data
│   └── src/talentlens/
│       ├── api/routes/           # FastAPI route handlers
│       │   ├── capabilities.py   # Skills matrix + role templates + JD generation
│       │   ├── candidates.py     # Candidate CRUD
│       │   ├── interviews.py     # Interview creation + pipeline trigger
│       │   ├── assessments.py    # Assessment retrieval + scorecards
│       │   ├── webhooks.py       # Fireflies + CoderPad webhooks
│       │   └── ...
│       ├── models/database/      # SQLAlchemy async models
│       │   ├── capability.py     # Capability, Technology, RoleTemplate
│       │   ├── candidate.py      # Candidate with pipeline stage
│       │   ├── assessment.py     # Assessment + CriterionScore
│       │   ├── evidence.py       # Evidence (transcript quotes)
│       │   └── ...
│       ├── schemas/              # Pydantic v2 request/response models
│       ├── services/
│       │   ├── assessment/       # Scoring engine, talk ratio, contributions
│       │   ├── ingestion/        # Fireflies transcript fetcher
│       │   ├── job_description.py# Claude-powered JD generation
│       │   ├── notifications/    # Slack integration
│       │   └── transcription/    # Deepgram (planned)
│       ├── config.py             # Pydantic Settings
│       ├── dependencies.py       # DB session dependency
│       └── main.py               # FastAPI app + middleware
├── frontend/
│   └── src/
│       ├── components/           # Reusable UI components
│       │   ├── CapabilityMatrix  # 5-dot proficiency grid
│       │   ├── SkillsRadar       # Capability score bars
│       │   ├── TechnologyPalette # DnD technology picker
│       │   ├── TechnologyRequirements # DnD drop zone
│       │   └── layout/           # AppShell, Sidebar, TopBar
│       ├── hooks/                # Data fetching hooks
│       ├── pages/                # Route pages
│       │   ├── DashboardPage     # Pipeline metrics + funnel
│       │   ├── CandidatesPage    # Candidate list + stage badges
│       │   ├── AssessmentPage    # Scorecard + skills matrix
│       │   └── RoleTemplatesPage # Template CRUD + DnD tech selection
│       └── types/                # TypeScript interfaces
├── infrastructure/               # GCP Cloud Run configs
├── docker-compose.yml
├── cloudbuild.yaml
└── deploy.sh
```
