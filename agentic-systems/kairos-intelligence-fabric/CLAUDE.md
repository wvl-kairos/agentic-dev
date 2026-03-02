# Kairos Intelligence Fabric — Project Context

## Project Overview
Interactive 3D knowledge visualization + AI agent platform for manufacturing data. "Living brain" of a manufacturing organization where ontologies, data, AI agents, and knowledge are visualized as an interactive 3D space.

**Target:** Investor demo for ACME Manufacturing (fictional company).
**Stack:** React + TypeScript + Three.js/R3F (frontend) + FastAPI + Python (backend) + Neo4j + ChromaDB + Anthropic Claude API.

## Architecture Documents (at repo root)
- `kairos-intelligence-fabric-prompt.md` — Original 5-phase build plan (3D viz, ontology construction, AI queries, knowledge crystallization, temporal playback)
- `kairos-unified-architecture-v1.md` — Unified architecture with dual ingestion (structured ontology + document RAG), entity resolution, hybrid retrieval, agentic query engine

## Architecture — Dual Ingestion Paths

### Path A: Structured Ontology (from schema files) — BUILT
User uploads SQL DDL / CSV data dictionary / JSON schema dictionary. Claude-powered 4-phase pipeline
(inspired by Ontology Pipeline framework, Jessica Talisman / Modern Data 101):

**Phase 1: Schema Analysis + Controlled Vocabulary**
- Parse all schema documents (SQL DDL, CSV data dict, JSON schema dict, MD profiles)
- Claude extracts tables, columns, types, FKs, descriptions
- Normalize entity names, resolve manufacturing abbreviations/synonyms
- Assign entity types (equipment, products, orders, suppliers, quality, people, production_lines, etc.)
- Assign domains (production, quality, supply_chain, maintenance, workforce, etc.)

**Phase 2: Taxonomy Construction**
- Build parent-child hierarchies from FK relationships and domain knowledge
- Equipment: Site > Area > Line > Cell > Unit (ISA-95)
- Products: Family > Product > Assembly > Component > Material
- Organizational: Department > Team > Role
- Standards: ISA-95, IEC 62264

**Phase 3: Relationship Discovery (Thesaurus + Ontology)**
- Map FK columns to semantic edge types (PRODUCES, REQUIRES, INSPECTED_BY, etc.)
- Discover cross-domain relationships
- Assign edge properties and evidence sources

**Phase 4: Graph Assembly**
- Assemble NodeModel/EdgeModel from all phases
- Optionally merge with existing sample_ontology.json
- Update in-memory graph store + persist to Neo4j (if enabled)
- Stream all events as SSE to frontend

**Files:** `services/ontology_engine.py`, `models/ontology_models.py`, `api/routes/ontology.py`
**API:** `POST /api/ontology/construct` (SSE stream), `GET /api/ontology/status`

### Path B: Document RAG (from unstructured text) — BUILT
ChromaDB (dense vectors) + BM25 (sparse keywords) + Reciprocal Rank Fusion.
2-hop agentic retrieval where Claude decides if hop 2 is needed via CoT bridging query.
Replaces the original LightRAG architecture (LightRAG was removed entirely).

### Path C: Cross-Domain Intelligence — NOT YET BUILT
Claude analyzes connections between structured ontology nodes and document knowledge.
Generates "golden edges" (ontological cross-links). Visualized in frontend.

## What's Been Built

### Backend Services (all in `backend/services/`)

| Service | File | Status |
|---------|------|--------|
| Format-aware chunking (CSV/JSON/SQL/text) | `chunking_service.py` | Done |
| ChromaDB vector store | `vector_store.py` | Done |
| BM25 + dense hybrid retrieval + RRF fusion | `hybrid_retriever.py` | Done |
| 2-hop agentic RAG with CoT bridging | `multihop_rag.py` | Done |
| RAG retriever (drop-in replacement) | `rag_retriever.py` | Done |
| Document manager (multi-format, multi-directory) | `document_manager.py` | Done |
| Ingestion pipeline (chunk + embed + entity extract) | `ingestion_pipeline.py` | Done |
| Entity reference extraction from doc text | `ingestion_pipeline.py` | Done |
| `DOCUMENTED_IN` edges in Neo4j | `ingestion_pipeline.py` | Done |
| **Ontology Engine (4-phase Claude pipeline)** | `ontology_engine.py` | Done |
| **Ontology data models** | `models/ontology_models.py` | Done |
| **Ontology API (SSE streaming)** | `api/routes/ontology.py` | Done |

### What's NOT Built Yet

| Component | Description |
|-----------|-------------|
| **Entity Resolver integration** | Fuzzy matching document entities to structured ontology nodes at query time |
| **Knowledge Crystallization** | `:Insight` nodes from agent discoveries, golden edges |
| **Temporal Playback** | Time-travel through factory data evolution |
| **Ontology Upload Panel** | Frontend drag-and-drop for schema files |

## Key Technical Decisions

1. **LightRAG removed** — Replaced with custom ChromaDB + BM25 + RRF hybrid. LightRAG had dependency/stability issues.
2. **Embeddings:** OpenAI `text-embedding-3-small` (not large) via ChromaDB's `OpenAIEmbeddingFunction`.
3. **BM25 is thread-safe** — Module-level `threading.Lock` for atomic rebuild/read of in-memory BM25Okapi index.
4. **All sync calls wrapped in `asyncio.to_thread()`** — ChromaDB and BM25 are sync libraries, must not block event loop.
5. **Singleton Anthropic client** — `multihop_rag.py` uses a module-level `AsyncAnthropic` singleton.
6. **Oversized chunks accepted for structured formats** — SQL CREATE TABLE blocks may exceed 800 chars; splitting would hurt retrieval quality.
7. **No Neo4j required for dev** — System works with in-memory graph store when `NEO4J_URI` not configured.

## File Format Chunking Strategies

| Format | Strategy | Key Detail |
|--------|----------|------------|
| `.txt`, `.md` | Paragraph boundaries | Split on `\n\n`, merge small paragraphs, split oversized at sentences |
| `.csv` | Rows with repeated headers | Header prepended to EVERY chunk, 5-20 rows per chunk (dynamic sizing) |
| `.json` | Structure-aware | Schema dicts: 1 chunk per table. Arrays: batch ~15 items. Flat: split by keys |
| `.sql` | CREATE TABLE blocks | 1 chunk per table/view, COMMENT ON kept with preceding block |

## Document Directories

- `backend/data/documents/` — Unstructured text documents (.txt) for RAG
- `backend/data/reference_schemas/` — Structured schema files (.sql, .csv, .json, .md) with `ref-` prefixed IDs
- `backend/data/uploads/` — User-uploaded files at runtime

## ACME Demo Documents (to be generated externally)

### 5 Structured (go in `data/reference_schemas/`)
1. `acme_manufacturing_schema.sql` — ~20-25 tables DDL (customers, orders, BOMs, production, equipment, quality, workforce, shipping)
2. `acme_data_dictionary.csv` — ~80 rows, columns: table_name, column_name, data_type, nullable, description, sample_values, domain
3. `acme_schema_dictionary.json` — Schema graph with ~6 domains, tables, columns, relationships
4. `acme_production_log.csv` — ~60 rows production log data (work_order_id, line_id, equipment_id, operator, start/end, units, defects, status)
5. `acme_equipment_sensors.json` — Array of ~40 sensor readings (equipment_id, sensor_type, value, unit, timestamp, status)

### 10 Unstructured (go in `data/documents/`)
1. `acme_company_profile.md` — Company overview, facilities, products, capabilities
2. `acme_maintenance_manual.txt` — Equipment maintenance procedures, troubleshooting
3. `acme_bom_specs.txt` — Bill of Materials specifications for key products
4. `acme_quality_spc.txt` — Quality SPC procedures, control limits, defect classification
5. `acme_supplier_audit.txt` — Supplier audit reports, quality ratings
6. `acme_production_schedule.txt` — Production schedule, shift assignments
7. `acme_oee_report.txt` — OEE (Overall Equipment Effectiveness) analysis
8. `acme_safety_incident.txt` — Safety incident reports, corrective actions
9. `acme_kaizen_report.txt` — Continuous improvement / kaizen event reports
10. `acme_training_log.txt` — Operator training records, certifications

### Entity ID Convention
All documents must use consistent entity IDs in parentheses for cross-referencing:
- Equipment: `(equip-cnc-a7)`, `(equip-weld-w2)`
- Products: `(prod-gear-set)`, `(prod-chassis-frame)`
- Orders: `(ord-4523)`, `(ord-7891)`
- Suppliers: `(supp-precision-steel)`, `(supp-alloy-works)`
- People: `(person-lzhang)`, `(person-mgarcia)`
- Lines: `(line-assembly-1)`, `(line-machining-2)`
- Quality: `(qual-insp-0012)`, `(qual-def-0045)`

## Config Keys (backend/config.py)
```
chromadb_persist_dir: str = "./chroma_data"
embedding_model: str = "text-embedding-3-small"
rag_top_k: int = 5
rag_rrf_k: int = 60
rag_max_chunk_size: int = 800
neo4j_enabled: bool  (derived from NEO4J_URI env var)
openai_api_key: str  (from OPENAI_API_KEY env var)
anthropic_api_key: str  (from ANTHROPIC_API_KEY env var)
```

## API Routes (all prefixed with /api)
- `health.router` — Health check
- `graph.router` — Graph data (nodes/edges for 3D visualization)
- `documents.router` — Document CRUD + upload
- `ingest.router` — Document ingestion (chunk + embed + entity extract)
- `query.router` — AI agent queries (agentic RAG)
- `knowledge.router` — Knowledge crystallization
- `ontology.router` — Ontology construction (SSE streaming) + status

## Ontology Engine Architecture
The ontology engine (`services/ontology_engine.py`) implements a 4-phase pipeline inspired by
Jessica Talisman's Ontology Pipeline (Controlled Vocabulary → Metadata → Taxonomy → Thesaurus → Ontology → KG):

1. **Phase 1** calls Claude with all schema content → returns `SchemaAnalysisResult` (tables, columns, types, domains, vocabulary)
2. **Phase 2** calls Claude with entities → returns `TaxonomyResult` (parent-child hierarchies)
3. **Phase 3** calls Claude with entities+taxonomy → returns `RelationshipResult` (typed edges)
4. **Phase 4** is pure Python assembly → produces `GraphResponse` (NodeModel/EdgeModel lists)

Each phase yields SSE events (`OntologySSEEvent`) that the API route streams to the frontend.
The final graph replaces the in-memory graph store via `graph_manager.update_graph()`.

**Usage:** `POST /api/ontology/construct` with `{"document_ids": [], "include_sample_ontology": false}`
- Empty `document_ids` = use all reference schema docs (.sql, .csv, .json, .md)
- `include_sample_ontology: true` = merge with existing sample_ontology.json nodes/edges

## Startup Flow (main.py lifespan)
1. Connect to Neo4j (if configured)
2. `_initialize_rag()`: If ChromaDB empty, chunk+embed all sample documents. Always rebuild BM25 index.

## To Force Re-indexing
Delete `chroma_data/` directory, then restart backend. All documents will be re-chunked and re-embedded.
