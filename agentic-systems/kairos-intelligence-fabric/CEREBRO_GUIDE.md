# Cerebro Intelligence Fabric — User Guide

**Live URL:** https://kairos-frontend-1088461990874.us-central1.run.app

Cerebro is an AI-powered knowledge visualization platform that turns manufacturing data into a living, interactive 3D knowledge graph. It combines structured ontology construction, document ingestion, and agentic AI retrieval to provide intelligent answers grounded in your organization's data.

---

## What You'll See

When you open Cerebro, you'll see a **3D interactive knowledge graph** — a network of nodes and edges representing the manufacturing organization's entities (equipment, products, orders, suppliers, people, production lines, quality metrics, etc.) and their relationships.

- **Rotate** the graph by clicking and dragging
- **Zoom** with the scroll wheel
- **Click a node** to see its details and connections in the right panel
- Nodes are color-coded by type (equipment = blue, products = green, suppliers = orange, etc.)

---

## Core Capabilities

### 1. Ontology Construction (4-Phase Claude Pipeline)

Cerebro builds a manufacturing ontology from structured schema files (SQL DDL, CSV data dictionaries, JSON schema dictionaries) using a 4-phase AI pipeline:

| Phase | What it does |
|-------|-------------|
| **Phase 1 — Schema Analysis** | Claude parses all schema documents, extracts tables/columns/types, normalizes entity names, resolves manufacturing abbreviations, and assigns entity types and domains |
| **Phase 2 — Taxonomy Construction** | Builds parent-child hierarchies from FK relationships and domain knowledge (ISA-95 equipment hierarchy, product BOMs, organizational structure) |
| **Phase 3 — Relationship Discovery** | Maps foreign keys to semantic edge types (PRODUCES, REQUIRES, INSPECTED_BY, etc.), discovers cross-domain relationships |
| **Phase 4 — Graph Assembly** | Assembles the final node/edge graph, persists to Neo4j, and renders in the 3D visualization |

The result is a semantically rich knowledge graph — not just a database schema, but a true ontology with typed relationships and hierarchical structure.

### 2. Document Ingestion & Knowledge Extraction

Upload documents to extract knowledge and link it to the existing ontology.

**How to use it:**
1. Click the **document icon** (top-left toolbar) to open the upload panel
2. Drag & drop files or click to browse (supported: `.txt`, `.pdf`, `.md`, `.csv`)
3. After uploading, click the **lightning bolt icon** next to the document
4. Cerebro will:
   - Chunk the document using format-aware strategies (CSV rows with repeated headers, JSON by structure, SQL by CREATE TABLE blocks, text by paragraphs)
   - Embed chunks into the vector store (ChromaDB)
   - Extract entity references from the text
   - Create a `Document` node in the knowledge graph
   - Link it to existing ontology nodes with `DOCUMENTED_IN` edges
5. A summary appears in the chat showing entities extracted, resolved, and new graph nodes created

**Format-aware chunking** ensures each format is split intelligently:
- **CSV** — Header repeated in every chunk so the LLM always has column context
- **JSON** — Schema dictionaries split by table; arrays batched with schema summary
- **SQL** — One chunk per CREATE TABLE/VIEW block
- **Text/Markdown** — Split on paragraph boundaries, merged for optimal size

### 3. Agentic AI Query System

The chat panel (bottom-right) lets you ask natural language questions. Cerebro uses a multi-stage agentic pipeline:

```
Query → Router → Retrieval → Context Merge → Specialist Agent → Response
```

**Query Router** classifies your question into one of four modes:
- **graph_lookup** — Questions about entities, relationships, structure ("What equipment is on Line 1?")
- **document_search** — Questions about document content ("What are the maintenance procedures for CNC mills?")
- **analytical** — Questions about metrics, trends, performance ("Show me the OEE trends")
- **hybrid** — Questions that need both graph and document data

**Hybrid Retrieval** combines two search strategies:
- **Dense vectors** (ChromaDB + OpenAI embeddings) — semantic similarity
- **Sparse keywords** (BM25) — exact term matching
- **Reciprocal Rank Fusion** merges both rankings for the best of both worlds

**2-Hop Agentic RAG** — If the first retrieval pass doesn't fully answer the question, Claude generates a bridging query and performs a second retrieval hop for deeper context.

**Specialist Agents** — Depending on the query mode, one or more specialist agents process the response:
- **Document Agent** — Analyzes document content, quotes specific data points
- **Graph Agent** — Traverses the knowledge graph for structural answers
- **Analytics Agent** — Interprets metrics, trends, and KPIs
- **Synthesis Agent** — Combines multiple sources into a coherent answer
- **Knowledge Agent** — Handles organizational knowledge and cross-domain questions

### 4. Knowledge Graph (Neo4j)

The graph is persisted in Neo4j (AuraDB) and visualized in real-time with Three.js/React Three Fiber.

**Node types:** Equipment, Products, Orders, Suppliers, Quality, People, Production Lines, Materials, Maintenance, Logistics, Safety, Organization, Documents, Knowledge

**Edge types:** Semantic relationships like PRODUCES, REQUIRES, OPERATES, INSPECTED_BY, SUPPLIED_BY, MAINTAINED_BY, DOCUMENTED_IN, and many more.

**Reset** — Click the Reset button (top toolbar) to restore the graph to its original baseline state, wiping any ingested document nodes and edges from both the in-memory store and Neo4j.

---

## Sample Questions to Try

The chat panel shows suggested questions. Here are some good ones:

| Question | What it tests |
|----------|--------------|
| "What equipment is on Assembly Line 1?" | Graph lookup — traverses equipment hierarchy |
| "Show me the OEE trends" | Analytical — retrieves OEE report data, breaks down by equipment |
| "What are the maintenance procedures for CNC mills?" | Document search — finds relevant maintenance manual chunks |
| "Which suppliers have quality issues?" | Hybrid — combines supplier graph nodes with audit document data |
| "What products require precision steel?" | Graph + document — BOM relationships and material specs |

---

## Architecture Summary

```
┌─────────────────────────────────────────────┐
│              Frontend (React + Three.js)     │
│  3D Graph Viz │ Chat Panel │ Upload Panel    │
└──────────────────────┬──────────────────────┘
                       │ REST + WebSocket
┌──────────────────────▼──────────────────────┐
│              Backend (FastAPI)               │
│                                             │
│  ┌─────────────┐  ┌──────────────────────┐  │
│  │ Query Router │→│ Hybrid Retrieval     │  │
│  │ (classify)   │ │ ChromaDB + BM25 + RRF│  │
│  └──────┬──────┘  └──────────┬───────────┘  │
│         │                    │              │
│  ┌──────▼──────────────────▼─────────────┐ │
│  │  Specialist Agents (Claude API)        │ │
│  │  Document│Graph│Analytics│Synthesis     │ │
│  └────────────────────────────────────────┘ │
│                                             │
│  ┌─────────────┐  ┌──────────────────────┐  │
│  │ Ontology    │  │ Ingestion Pipeline   │  │
│  │ Engine      │  │ Chunk→Embed→Extract  │  │
│  │ (4-phase)   │  │ →Link to Graph       │  │
│  └──────┬──────┘  └──────────┬───────────┘  │
└─────────┼────────────────────┼──────────────┘
          │                    │
   ┌──────▼──────┐    ┌───────▼───────┐
   │   Neo4j     │    │   ChromaDB    │
   │ (AuraDB)    │    │ (Vectors)     │
   │ Graph Store │    │ + BM25 Index  │
   └─────────────┘    └───────────────┘
```

**Stack:** React + TypeScript + Three.js (frontend) | FastAPI + Python (backend) | Neo4j AuraDB (graph) | ChromaDB (vectors) | Claude API (reasoning) | OpenAI (embeddings) | GCP Cloud Run (hosting)
