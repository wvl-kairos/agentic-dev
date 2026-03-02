# Cerebro Intelligence Fabric

**"See Your Factory Think"**

A visually stunning, interactive 3D knowledge visualization and AI agent platform for manufacturing data. Cerebro renders manufacturing ontologies as an immersive force-directed graph in 3D space.

## Quick Start

### Prerequisites
- Node.js 20+
- Python 3.9+
- Docker (optional, for containerized deployment)

### Local Development

**Backend:**
```bash
cd backend
pip3 install -r requirements.txt
uvicorn main:app --reload --port 8000
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173 - the frontend proxies API requests to the backend.

### Docker

```bash
docker compose up --build
```
- Frontend: http://localhost:3000
- Backend: http://localhost:8000

### Deploy to GCP Cloud Run

```bash
./deploy.sh <GCP_PROJECT_ID> <REGION>
```

## Architecture

```
Frontend (React + React Three Fiber)
  - 3D force-directed graph (d3-force-3d)
  - 7 node types with distinct geometries
  - 6 edge types with flow particles
  - Post-processing (Bloom, ChromaticAberration)
  - Glassmorphism UI panels
  - Zustand state management

Backend (FastAPI + Python)
  - /api/health - Health check
  - /api/graph  - Manufacturing ontology data
  - In-memory graph store (Neo4j-ready interface)

Infrastructure
  - Docker containers for both services
  - GCP Cloud Run deployment
  - Cloud Build CI/CD
```

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 18, TypeScript, Vite |
| 3D | React Three Fiber, drei, postprocessing |
| Layout | d3-force-3d |
| State | Zustand |
| Styling | Tailwind CSS, Framer Motion |
| Backend | FastAPI, Pydantic |
| Deploy | Docker, GCP Cloud Run |

## Sample Data

60 manufacturing nodes across 7 types:
- **Equipment** (12): CNC mills, lathes, presses, welders, assembly stations
- **Products** (10): Hydraulic cylinders, drive shafts, gear assemblies
- **Orders** (10): Work orders with priorities and completion status
- **Quality** (8): SPC measurements, OEE scores, defect records
- **People** (8): Operators, supervisors, quality manager
- **Suppliers** (7): Steel, aluminum, seals, electronics, fasteners
- **Production Lines** (5): Machining, assembly, finishing, packaging, testing

141 edges across 6 relationship types: PRODUCES, REQUIRES, INSPECTED_BY, SUPPLIED_BY, BELONGS_TO, DEPENDS_ON

## Phase Roadmap

- [x] **Phase 1:** Foundation + 3D Graph Viewer
- [ ] **Phase 2:** Ontology Auto-Construction Engine
- [ ] **Phase 3:** AI Agent Queries with Visual Reasoning
- [ ] **Phase 4:** Knowledge Crystallization + Memory
- [ ] **Phase 5:** Temporal Playback + Polish
