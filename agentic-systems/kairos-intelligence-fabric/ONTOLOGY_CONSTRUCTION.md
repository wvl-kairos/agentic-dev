# Ontology Construction Pipeline — Technical Deep Dive

Cerebro constructs manufacturing ontologies from raw schema files using a **4-phase AI pipeline powered by Claude**. This approach is inspired by the Ontology Pipeline framework (Jessica Talisman / Modern Data 101), which defines the progression:

```
Controlled Vocabulary → Metadata Standards → Taxonomy → Thesaurus → Ontology → Knowledge Graph
```

We compress this into 4 practical phases that transform schema files into a semantically rich, navigable knowledge graph.

---

## Input: Schema Documents

The pipeline accepts four file formats, each parsed with format-aware logic:

| Format | File | What it contains |
|--------|------|-----------------|
| **SQL DDL** | `acme_manufacturing_schema.sql` | ~20 CREATE TABLE statements with columns, types, FKs, constraints, and COMMENT ON descriptions. Organized by domain (Customer & Sales, Production, Equipment, Quality, etc.) |
| **CSV Data Dictionary** | `acme_data_dictionary.csv` | ~80 rows mapping every column across all tables: table_name, column_name, data_type, nullable, description, sample_values, domain |
| **JSON Schema Dictionary** | `acme_schema_dictionary.json` | Structured schema graph with ~6 domains, each containing tables with columns, relationships, and cross-domain links |
| **Markdown Profile** | `acme_company_profile.md` | Company overview, facility descriptions, product lines, capabilities, certifications |

These files live in `backend/data/reference_schemas/` and are loaded automatically on startup. The ontology engine can also use any uploaded documents with schema-like extensions (.sql, .csv, .json, .md).

### Why Multiple Formats?

Each format contributes unique information:
- **SQL DDL** provides the authoritative table structure, constraints, and foreign key relationships
- **CSV Data Dictionary** adds human-readable descriptions, sample values, and domain classification for every column
- **JSON Schema Dictionary** contributes pre-defined cross-domain relationships and a hierarchical domain structure
- **Markdown Profile** provides business context (facility layout, product families, organizational structure) that helps Claude make better ontological decisions

All four are concatenated and sent to Claude as a single context, labeled by filename and type.

---

## Phase 1: Schema Analysis + Controlled Vocabulary

**Goal:** Extract every entity (table) from the schema documents, normalize names, classify types, and assign domains.

**What Claude does:**
1. Parses all four schema documents simultaneously
2. Identifies every table/entity across all formats (SQL DDL, CSV rows grouped by table_name, JSON table objects)
3. Builds a **controlled vocabulary** — maps abbreviations and synonyms to canonical forms:
   - `maint_wo` → `maintenance_work_order`
   - `bom` → `bill_of_materials`
   - `equip` → `equipment`
4. Classifies each entity into one of 12 types: `equipment`, `products`, `orders`, `suppliers`, `quality`, `people`, `production_lines`, `materials`, `maintenance`, `logistics`, `safety`, `organizational`
5. Assigns a domain: `production`, `quality`, `supply_chain`, `maintenance`, `workforce`, `logistics`, `sales`, `engineering`
6. Extracts all columns with data types, PKs, FKs, and references

**Output:** `SchemaAnalysisResult`
```
tables: [
  {
    table_name: "equipment",
    entity_type: "equipment",
    label: "Equipment",
    description: "Manufacturing equipment units...",
    domain: "production",
    columns: [{ name, data_type, is_pk, is_fk, references_table, ... }],
    synonyms: ["machine", "unit", "asset"]
  },
  ...
]
domains_found: ["production", "quality", "supply_chain", ...]
vocabulary: { "wo": "work_order", "bom": "bill_of_materials", ... }
```

**Entity ID Generation:** After Phase 1, the system generates deterministic entity IDs using a prefix map:

| Entity Type | Prefix | Example ID |
|-------------|--------|------------|
| equipment | `equip` | `equip-equipment` |
| products | `prod` | `prod-products` |
| orders | `ord` | `ord-customer-orders` |
| suppliers | `supp` | `supp-suppliers` |
| quality | `qual` | `qual-quality-inspections` |
| people | `person` | `person-operators` |
| production_lines | `line` | `line-production-lines` |
| materials | `mat` | `mat-materials` |
| maintenance | `maint` | `maint-maintenance-work-orders` |
| logistics | `logis` | `logis-shipping-records` |
| safety | `safety` | `safety-safety-incidents` |
| organizational | `org` | `org-departments` |

These IDs are passed to subsequent phases so Claude uses consistent identifiers.

---

## Phase 2: Taxonomy Construction

**Goal:** Build parent-child hierarchies following ISA-95 and manufacturing best practices.

**What Claude does:**

Given the extracted entities (with their pre-assigned IDs), Claude constructs hierarchies:

1. **Equipment hierarchy** (ISA-95): Site → Area → Production Line → Work Center → Equipment Unit
2. **Product hierarchy**: Product Family → Product → Assembly → Component → Raw Material
3. **Organizational hierarchy**: Department → Team → Role
4. **Process hierarchy**: Process → Sub-Process → Operation → Step
5. **Quality hierarchy**: Standard → Specification → Inspection → Measurement
6. **Supply chain hierarchy**: Supplier Category → Supplier → Contract → PO

**Rules enforced:**
- Must use the exact entity IDs from Phase 1
- May create NEW hierarchy-only nodes (e.g., a parent "Production Area" grouping) with the same prefix convention
- Only creates hierarchies supported by the actual schema data — no invented entities
- Maximum 2-4 levels deep

**Output:** `TaxonomyResult`
```
hierarchies: [
  {
    entity_id: "line-production-lines",
    label: "Production Lines",
    entity_type: "production_lines",
    parent_id: "",
    children_ids: ["equip-cnc-mill", "equip-lathe"],
    level: 0
  },
  {
    entity_id: "equip-cnc-mill",
    label: "CNC Mill",
    entity_type: "equipment",
    parent_id: "line-production-lines",
    children_ids: [],
    level: 1
  },
  ...
]
hierarchy_types: ["equipment", "product", "organizational"]
```

Taxonomy nodes that don't already exist as schema entities become new graph nodes (hierarchy grouping nodes).

---

## Phase 3: Relationship Discovery

**Goal:** Discover all meaningful semantic relationships between entities, transforming FK columns into typed ontological edges.

**What Claude does:**

Given entities + taxonomy, Claude discovers relationships of these types:

| Relationship | Meaning | Evidence Source |
|-------------|---------|----------------|
| `PRODUCES` | Equipment/Line → Product | FK: product_id in production_log |
| `REQUIRES` | Product → Material/Component | FK: material_id in bom |
| `INSPECTED_BY` | Product/Equipment → Quality record | FK: equipment_id in quality_inspections |
| `SUPPLIED_BY` | Material → Supplier | FK: supplier_id in materials |
| `BELONGS_TO` | Equipment → Line, Person → Department | FK + taxonomy hierarchy |
| `DEPENDS_ON` | Order → Order, Process → Process | FK: parent_order_id |
| `MAINTAINED_BY` | Equipment → Maintenance record | FK: equipment_id in maintenance_wo |
| `ASSIGNED_TO` | Person → Equipment/Line | FK: operator_id in production_log |
| `FULFILLS` | Order → Product, Work Order → Order | FK: order_id in work_orders |
| `MONITORS` | Quality record → Equipment/Product | FK: equipment_id in quality checks |
| `STORES` | Location → Material/Product | FK: location_id in inventory |

**Cross-domain relationships** are also discovered — connections that bridge different areas:
- Quality events linked to equipment (quality → production)
- Suppliers linked to products through materials (supply_chain → production)
- Safety incidents linked to equipment and personnel (safety → production → workforce)
- Maintenance records linked to operators and equipment (maintenance → workforce → production)

**Output:** `RelationshipResult`
```
relationships: [
  {
    source_id: "equip-cnc-mill",
    target_id: "prod-gear-set",
    relationship_type: "PRODUCES",
    properties: { "rate": "45 units/hr" },
    source_evidence: "FK: equipment_id in production_log"
  },
  ...
]
relationship_types_found: ["PRODUCES", "REQUIRES", "BELONGS_TO", ...]
```

---

## Phase 4: Graph Assembly

**Goal:** Assemble the final knowledge graph from all three phases.

This phase is **pure Python** — no Claude calls. It:

1. **Creates nodes from schema entities** — Each table from Phase 1 becomes a graph node with properties (domain, description, column_count, synonyms, source)

2. **Creates nodes from taxonomy** — Hierarchy-only nodes introduced in Phase 2 (that don't correspond to a schema table) become additional graph nodes

3. **Creates taxonomy edges** — Every parent-child relationship from Phase 2 becomes a `BELONGS_TO` edge

4. **Creates relationship edges** — Every relationship from Phase 3 becomes a typed edge, but **only if both endpoint nodes exist** in the graph. Dangling references are dropped with a warning.

5. **Optional: Merge with sample ontology** — If `include_sample_ontology: true`, merges with the hand-crafted `sample_ontology.json` (60 nodes, 141 edges) to combine machine-constructed and human-curated data.

6. **Updates stores:**
   - Updates the **in-memory graph store** (`graph_manager.update_graph()`)
   - **Saves a baseline snapshot** (`graph_manager.save_baseline()`) so the Reset button can restore this state
   - **Persists to Neo4j** (if enabled) using MERGE operations for idempotency

**Output:** `GraphResponse`
```
nodes: [NodeModel(id, type, label, properties), ...]
edges: [EdgeModel(source, target, type, properties), ...]
metadata: {
  total_nodes: 60,
  total_edges: 141,
  ontology_version: "auto-constructed",
  last_updated: "2026-02-20T..."
}
```

---

## Real-Time Streaming (SSE)

The entire pipeline streams progress to the frontend via **Server-Sent Events (SSE)**:

```
API: POST /api/ontology/construct
Response: text/event-stream
```

Events emitted during construction:

| Event | Phase | Data |
|-------|-------|------|
| `construction_start` | — | documents, total_documents, total_chars |
| `phase_start` | schema_analysis | message |
| `entity_discovered` | schema_analysis | entity_type, label, domain, table_name, column_count |
| `phase_complete` | schema_analysis | entities_found, domains, vocabulary_terms |
| `phase_start` | taxonomy | message |
| `taxonomy_node` | taxonomy | entity_id, label, entity_type, parent_id, level |
| `phase_complete` | taxonomy | hierarchy_nodes, hierarchy_types |
| `phase_start` | relationships | message |
| `relationship_found` | relationships | source_id, target_id, type, evidence |
| `phase_complete` | relationships | relationships_found, types |
| `phase_start` | graph_assembly | message |
| `phase_complete` | graph_assembly | total_nodes, total_edges |
| `construction_complete` | — | total_nodes, total_edges, domains, relationship_types |

The frontend can render these events in real-time — showing entities appearing, taxonomy trees growing, and relationships being drawn as Claude discovers them.

---

## Post-Construction: Document Ingestion

After the ontology is constructed, users can **ingest unstructured documents** that link to the ontology:

1. **Upload** a document (.txt, .pdf, .md, .csv)
2. **Ingest** triggers the pipeline:
   - **Chunk** the document (format-aware: CSV with repeated headers, JSON by structure, SQL by CREATE TABLE, text by paragraphs)
   - **Embed** chunks into ChromaDB (OpenAI `text-embedding-3-small`)
   - **Index** in BM25 for keyword search
   - **Extract** entity references from the text — pattern-matched IDs like `(equip-cnc-a7)`, `(prod-gear-set)`
   - **Resolve** each entity against the ontology graph:
     - If the node exists → link with `DOCUMENTED_IN` edge
     - If it doesn't exist → create an instance node, link with `INSTANCE_OF` edge to the closest type node, then add `DOCUMENTED_IN` edge
3. A `Document` node is created in Neo4j, and all extracted entities get `DOCUMENTED_IN` edges pointing to it

This creates a bridge between the structured ontology and unstructured knowledge, enabling the agentic query system to traverse both.

---

## Configuration

| Parameter | Value | Description |
|-----------|-------|-------------|
| Claude model | `claude-sonnet-4-20250514` | Used for all 3 AI phases |
| Temperature | `0.1` | Low temperature for deterministic ontology construction |
| Max tokens | `16,384` | Per phase — accommodates large schema outputs |
| Context limit | `~60K chars` | Schema content truncated if too long |
| API endpoint | `POST /api/ontology/construct` | SSE streaming endpoint |
| Status endpoint | `GET /api/ontology/status` | Check construction progress |

---

## Data Flow Diagram

```
┌───────────────────────────────────────────────────────┐
│              Schema Documents (4 files)                │
│  .sql (DDL)  .csv (data dict)  .json (schema)  .md   │
└──────────────────────┬────────────────────────────────┘
                       │ concatenate + label by type
                       ▼
         ┌─────────────────────────────┐
         │  Phase 1: Schema Analysis   │ ← Claude API call
         │  + Controlled Vocabulary    │
         │                             │
         │  Extract tables, columns,   │
         │  types, FKs, domains.       │
         │  Normalize names.           │
         └──────────┬──────────────────┘
                    │ SchemaAnalysisResult
                    │ + generated entity IDs
                    ▼
         ┌─────────────────────────────┐
         │  Phase 2: Taxonomy          │ ← Claude API call
         │  Construction               │
         │                             │
         │  ISA-95 hierarchies:        │
         │  Equipment, Product,        │
         │  Organizational, Process,   │
         │  Quality, Supply Chain      │
         └──────────┬──────────────────┘
                    │ TaxonomyResult
                    ▼
         ┌─────────────────────────────┐
         │  Phase 3: Relationship      │ ← Claude API call
         │  Discovery                  │
         │                             │
         │  FK → semantic edges        │
         │  Cross-domain links         │
         │  PRODUCES, REQUIRES,        │
         │  INSPECTED_BY, etc.         │
         └──────────┬──────────────────┘
                    │ RelationshipResult
                    ▼
         ┌─────────────────────────────┐
         │  Phase 4: Graph Assembly    │ ← Pure Python
         │                             │
         │  Nodes from schema + tax    │
         │  Edges from tax + rels      │
         │  Drop dangling references   │
         │  Optional: merge sample     │
         └──────────┬──────────────────┘
                    │ GraphResponse
                    ▼
       ┌────────────┴────────────┐
       ▼                         ▼
┌──────────────┐       ┌──────────────┐
│  In-Memory   │       │    Neo4j     │
│ Graph Store  │       │   (AuraDB)   │
│ + Baseline   │       │  MERGE ops   │
│   Snapshot   │       │              │
└──────┬───────┘       └──────────────┘
       │
       ▼
┌──────────────┐
│  3D Graph    │
│ Visualization│
│ (Three.js)   │
└──────────────┘
```

---

## Key Files

| File | Purpose |
|------|---------|
| `backend/services/ontology_engine.py` | Core pipeline: prompts, 4 phases, Claude calls, graph assembly, Neo4j persistence |
| `backend/models/ontology_models.py` | Pydantic models: TableEntity, TaxonomyNode, OntologyRelationship, SSE events |
| `backend/api/routes/ontology.py` | API routes: POST /construct (SSE), GET /status |
| `backend/models/graph_models.py` | NodeModel, EdgeModel, GraphResponse — the final graph structure |
| `backend/services/graph_manager.py` | In-memory graph store with baseline snapshot for reset |
| `backend/services/ingestion_pipeline.py` | Post-construction document ingestion: entity extraction + DOCUMENTED_IN edges |
| `backend/data/reference_schemas/` | Input schema files (.sql, .csv, .json, .md) |
| `backend/data/sample_ontology.json` | Hand-crafted baseline ontology (60 nodes, 141 edges) |
