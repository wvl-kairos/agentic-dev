"""Ontology Engine — Claude-powered pipeline for constructing manufacturing ontologies.

Implements a 4-phase pipeline inspired by the Ontology Pipeline framework
(Jessica Talisman / Modern Data 101):

  Phase 1: Schema Analysis + Controlled Vocabulary
    - Parse schema documents (SQL DDL, CSV data dict, JSON schema dict)
    - Extract tables, columns, types, FKs
    - Normalize entity names, resolve manufacturing synonyms
    - Assign entity types and domains

  Phase 2: Taxonomy Construction
    - Build parent-child hierarchies (equipment, product, organizational)
    - ISA-95 / IEC 62264 alignment for manufacturing

  Phase 3: Relationship Discovery (Thesaurus + Ontology)
    - Map FK relationships to semantic edge types
    - Discover cross-domain relationships
    - Assign edge properties

  Phase 4: Graph Assembly
    - Assemble NodeModel / EdgeModel for the 3D graph
    - Stream results as SSE events
    - Update in-memory graph store and optionally Neo4j
"""

from __future__ import annotations

import asyncio
import json
import logging
import re
from collections.abc import AsyncGenerator
from datetime import datetime, timezone

import anthropic

from config import settings
from models.graph_models import EdgeModel, GraphMetadata, GraphResponse, NodeModel
from models.ontology_models import (
    ColumnInfo,
    ConstructionPhase,
    OntologyConstructStatus,
    OntologyEntity,
    OntologyRelationship,
    OntologySSEEvent,
    RelationshipResult,
    SchemaAnalysisResult,
    TableEntity,
    TaxonomyNode,
    TaxonomyResult,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Singleton Anthropic client
# ---------------------------------------------------------------------------

_anthropic_client: anthropic.AsyncAnthropic | None = None


def _get_client() -> anthropic.AsyncAnthropic:
    global _anthropic_client
    if _anthropic_client is None:
        _anthropic_client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
    return _anthropic_client


# ---------------------------------------------------------------------------
# Construction state (in-memory singleton)
# ---------------------------------------------------------------------------

_construction_status = OntologyConstructStatus()


def get_construction_status() -> OntologyConstructStatus:
    return _construction_status


# ---------------------------------------------------------------------------
# Prompts
# ---------------------------------------------------------------------------

SCHEMA_ANALYSIS_PROMPT = """\
You are a manufacturing data architect analyzing database schemas to build an ontology.

Given the schema content below (which may include SQL DDL, CSV data dictionaries, \
JSON schema definitions, and/or markdown documentation), perform Phase 1 of ontology \
construction:

1. **Extract all tables/entities** — Identify every table or entity described.
2. **Controlled Vocabulary** — Normalize each entity name to a clean, canonical form. \
Resolve abbreviations and synonyms (e.g., "maint_wo" → "maintenance_work_order", \
"bom" → "bill_of_materials").
3. **Classify each entity** into one of these types: \
equipment, products, orders, suppliers, quality, people, production_lines, materials, \
maintenance, logistics, safety, organizational.
4. **Assign a domain** to each entity: production, quality, supply_chain, maintenance, \
workforce, logistics, sales, engineering.
5. **Extract columns** with their data types, PKs, FKs, and descriptions.
6. **Identify synonyms** for each entity (alternative names used in manufacturing).

SCHEMA CONTENT:
---
{schema_content}
---

Respond with valid JSON matching this structure exactly:
{{
  "tables": [
    {{
      "table_name": "original_table_name",
      "entity_type": "equipment",
      "label": "Human Readable Name",
      "description": "What this entity represents",
      "domain": "production",
      "columns": [
        {{
          "name": "column_name",
          "data_type": "VARCHAR(100)",
          "nullable": true,
          "is_primary_key": false,
          "is_foreign_key": false,
          "references_table": "",
          "references_column": "",
          "description": "What this column stores"
        }}
      ],
      "synonyms": ["alt_name_1", "alt_name_2"]
    }}
  ],
  "domains_found": ["production", "quality", "supply_chain"],
  "vocabulary": {{
    "wo": "work_order",
    "bom": "bill_of_materials",
    "maint": "maintenance"
  }}
}}

Important:
- Extract ALL tables, not just a sample.
- For CSV data dictionaries, each row describes a column — group by table_name.
- For JSON schema dicts, each table object is an entity.
- For SQL DDL, each CREATE TABLE is an entity. Parse COMMENT ON for descriptions.
- Be thorough with FK detection — they define the ontology structure."""

TAXONOMY_PROMPT = """\
You are a manufacturing ontology engineer. Given the extracted entities below, \
build the taxonomy (parent-child hierarchies) following ISA-95 and manufacturing \
best practices.

ENTITIES:
---
{entities_json}
---

Build hierarchies for:
1. **Equipment hierarchy**: Site → Area → Production Line → Work Center → Equipment Unit
2. **Product hierarchy**: Product Family → Product → Assembly → Component → Raw Material
3. **Organizational hierarchy**: Department → Team → Role
4. **Process hierarchy**: Process → Sub-Process → Operation → Step
5. **Quality hierarchy**: Standard → Specification → Inspection → Measurement
6. **Supply chain hierarchy**: Supplier Category → Supplier → Contract → PO

Use the entity IDs from the schema analysis. Create hierarchy nodes only where the data \
supports it — don't invent entities that aren't in the schema.

Respond with valid JSON:
{{
  "hierarchies": [
    {{
      "entity_id": "node-id",
      "label": "Display Name",
      "entity_type": "equipment",
      "parent_id": "",
      "children_ids": ["child-1", "child-2"],
      "level": 0
    }}
  ],
  "hierarchy_types": ["equipment", "product", "organizational"]
}}

Rules:
- IMPORTANT: Each entity in the input has a pre-assigned "entity_id" field. \
You MUST use these exact IDs when referencing existing entities.
- For NEW hierarchy-only nodes (e.g., a parent "Production" domain grouping), \
use the same prefix convention: type-slug (e.g., "equip-machining-area", "prod-family-hydraulic")
- Top-level nodes have empty parent_id
- Only create hierarchies supported by the actual schema data
- Keep it practical — 2-4 levels deep maximum"""

RELATIONSHIP_PROMPT = """\
You are a manufacturing ontology engineer. Given the entities and taxonomy below, \
discover all meaningful relationships between entities.

ENTITIES:
---
{entities_json}
---

TAXONOMY:
---
{taxonomy_json}
---

Discover relationships of these types:
- **PRODUCES**: Equipment/Line → Product
- **REQUIRES**: Product → Material/Component (BOM)
- **INSPECTED_BY**: Product/Equipment → Quality record
- **SUPPLIED_BY**: Material/Component → Supplier
- **BELONGS_TO**: Equipment → Line, Person → Department, Order → Customer
- **DEPENDS_ON**: Order → Order, Process → Process, Equipment → Equipment
- **MAINTAINED_BY**: Equipment → Maintenance record/Person
- **ASSIGNED_TO**: Person → Equipment/Line
- **FULFILLS**: Order → Product, WO → Order
- **MONITORS**: Quality record → Equipment/Product
- **STORES**: Location → Material/Product

Also discover cross-domain relationships that connect different areas \
(e.g., quality events linked to equipment, suppliers linked to products).

Respond with valid JSON:
{{
  "relationships": [
    {{
      "source_id": "entity-id-1",
      "target_id": "entity-id-2",
      "relationship_type": "PRODUCES",
      "properties": {{"rate": "45 units/hr"}},
      "source_evidence": "FK: equipment_id in production_log"
    }}
  ],
  "relationship_types_found": ["PRODUCES", "REQUIRES", "BELONGS_TO"]
}}

Rules:
- IMPORTANT: Each entity has a pre-assigned "entity_id" field. Use these exact IDs \
as source_id and target_id. Also use entity_ids from the taxonomy output.
- Infer relationships from: FK columns, column naming patterns, domain knowledge
- Add meaningful properties where the schema data supports it
- Include at least one cross-domain relationship per domain pair where logical
- Prefer specific relationship types over generic ones"""


# ---------------------------------------------------------------------------
# Phase implementations
# ---------------------------------------------------------------------------

async def _call_claude(prompt: str, max_tokens: int = 16384) -> dict:
    """Call Claude with a prompt expecting JSON output. Returns parsed dict."""
    client = _get_client()
    response = await client.messages.create(
        model=settings.agent_model,
        max_tokens=max_tokens,
        temperature=0.1,
        messages=[{"role": "user", "content": prompt}],
    )

    text = response.content[0].text.strip()

    if response.stop_reason == "max_tokens":
        logger.warning(
            "Claude response truncated (max_tokens=%d). Output length: %d chars",
            max_tokens, len(text),
        )

    # Extract JSON from possible markdown code fence (handles truncated fences too)
    json_match = re.search(r"```(?:json)?\s*\n?(.*?)```", text, re.DOTALL)
    if json_match:
        text = json_match.group(1).strip()
    elif text.startswith("```"):
        # Truncated code fence — strip opening marker
        text = re.sub(r"^```(?:json)?\s*\n?", "", text).strip()

    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        logger.error("Claude returned invalid JSON: %s...", text[:300])
        raise ValueError("Ontology engine received invalid JSON from Claude")

    if not isinstance(data, dict):
        raise ValueError(f"Expected dict from Claude, got {type(data).__name__}")
    return data


def _split_schema_into_chunks(schema_parts: list[str], max_chars: int = 200_000) -> list[str]:
    """Group document parts into chunks that fit within the token budget.

    Splits at document boundaries (each part is one document).  If a single
    document exceeds *max_chars* it is included alone in its own chunk.
    """
    chunks: list[str] = []
    current: list[str] = []
    current_len = 0

    for part in schema_parts:
        part_len = len(part)
        if current and current_len + part_len > max_chars:
            chunks.append("\n".join(current))
            current = [part]
            current_len = part_len
        else:
            current.append(part)
            current_len += part_len

    if current:
        chunks.append("\n".join(current))

    return chunks


def _parse_phase1_response(data: dict) -> SchemaAnalysisResult:
    """Parse a single Phase 1 Claude response into a SchemaAnalysisResult."""
    tables = []
    for t in data.get("tables", []):
        if not t.get("table_name"):
            logger.warning("Skipping table with missing table_name: %s", t)
            continue
        columns = [ColumnInfo(**c) for c in t.get("columns", [])]
        table = TableEntity(
            table_name=t["table_name"],
            entity_type=t.get("entity_type", "unknown"),
            label=t.get("label") or t["table_name"].replace("_", " ").title(),
            description=t.get("description", ""),
            domain=t.get("domain", ""),
            columns=columns,
            synonyms=t.get("synonyms", []),
        )
        tables.append(table)

    return SchemaAnalysisResult(
        tables=tables,
        domains_found=data.get("domains_found", []),
        vocabulary=data.get("vocabulary", {}),
    )


def _merge_schema_results(results: list[SchemaAnalysisResult]) -> SchemaAnalysisResult:
    """Merge multiple Phase 1 results into a single deduplicated result."""
    all_tables: list[TableEntity] = []
    seen_tables: set[str] = set()
    all_domains: set[str] = set()
    merged_vocab: dict[str, str] = {}

    for r in results:
        for table in r.tables:
            if table.table_name not in seen_tables:
                seen_tables.add(table.table_name)
                all_tables.append(table)
        all_domains.update(r.domains_found)
        merged_vocab.update(r.vocabulary)

    return SchemaAnalysisResult(
        tables=all_tables,
        domains_found=sorted(all_domains),
        vocabulary=merged_vocab,
    )


async def _phase1_schema_analysis(
    schema_content: str,
) -> SchemaAnalysisResult:
    """Phase 1: Parse schemas and build controlled vocabulary.

    If content fits in a single call, sends it directly.
    Otherwise splits into chunks at document boundaries and merges results.
    """
    prompt = SCHEMA_ANALYSIS_PROMPT.format(schema_content=schema_content)
    data = await _call_claude(prompt)
    return _parse_phase1_response(data)


async def _phase1_chunked(
    schema_parts: list[str],
    on_chunk_done: object = None,
) -> SchemaAnalysisResult:
    """Run Phase 1 across multiple chunks and merge results.

    *schema_parts* is the list of per-document strings (already formatted with
    the ``--- Document: ... ---`` header).  *on_chunk_done* is an optional
    async callback ``(chunk_index, total_chunks, partial_result)`` for
    progress reporting.
    """
    chunks = _split_schema_into_chunks(schema_parts)

    if len(chunks) == 1:
        return await _phase1_schema_analysis(chunks[0])

    logger.info("Phase 1 will process %d chunks", len(chunks))
    partial_results: list[SchemaAnalysisResult] = []

    for i, chunk in enumerate(chunks):
        logger.info("Phase 1 chunk %d/%d (%d chars)", i + 1, len(chunks), len(chunk))
        result = await _phase1_schema_analysis(chunk)
        partial_results.append(result)

        if on_chunk_done and callable(on_chunk_done):
            await on_chunk_done(i, len(chunks), result)

    merged = _merge_schema_results(partial_results)
    logger.info(
        "Phase 1 merged: %d tables, %d domains from %d chunks",
        len(merged.tables), len(merged.domains_found), len(chunks),
    )
    return merged


def _build_entity_id_map(tables: list[TableEntity]) -> dict[str, str]:
    """Build mapping of table_name → generated entity_id for consistency across phases."""
    return {
        t.table_name: _make_entity_id(t.entity_type, t.table_name)
        for t in tables
    }


async def _phase2_taxonomy(
    schema_result: SchemaAnalysisResult,
    entity_id_map: dict[str, str],
) -> TaxonomyResult:
    """Phase 2: Build hierarchical taxonomy from entities."""
    # Include the pre-generated entity IDs in the context for Claude
    entities_with_ids = []
    for t in schema_result.tables:
        d = t.model_dump()
        d["entity_id"] = entity_id_map.get(t.table_name, "")
        entities_with_ids.append(d)

    entities_json = json.dumps(entities_with_ids, indent=2)
    prompt = TAXONOMY_PROMPT.format(entities_json=entities_json)
    data = await _call_claude(prompt)

    hierarchies = [TaxonomyNode(**h) for h in data.get("hierarchies", [])]
    return TaxonomyResult(
        hierarchies=hierarchies,
        hierarchy_types=data.get("hierarchy_types", []),
    )


async def _phase3_relationships(
    schema_result: SchemaAnalysisResult,
    taxonomy_result: TaxonomyResult,
    entity_id_map: dict[str, str],
) -> RelationshipResult:
    """Phase 3: Discover semantic relationships between entities."""
    # Include pre-generated entity IDs for Claude to use
    entities_with_ids = []
    for t in schema_result.tables:
        d = t.model_dump()
        d["entity_id"] = entity_id_map.get(t.table_name, "")
        entities_with_ids.append(d)

    entities_json = json.dumps(entities_with_ids, indent=2)
    taxonomy_json = json.dumps(
        [h.model_dump() for h in taxonomy_result.hierarchies], indent=2
    )
    prompt = RELATIONSHIP_PROMPT.format(
        entities_json=entities_json, taxonomy_json=taxonomy_json
    )
    data = await _call_claude(prompt)

    relationships = [
        OntologyRelationship(**r) for r in data.get("relationships", [])
    ]
    return RelationshipResult(
        relationships=relationships,
        relationship_types_found=data.get("relationship_types_found", []),
    )


def _phase4_assemble_graph(
    schema_result: SchemaAnalysisResult,
    taxonomy_result: TaxonomyResult,
    relationship_result: RelationshipResult,
    include_sample: bool = False,
) -> GraphResponse:
    """Phase 4: Assemble final graph from all phases."""
    nodes: list[NodeModel] = []
    edges: list[EdgeModel] = []
    seen_ids: set[str] = set()

    # --- Nodes from schema entities ---
    for table in schema_result.tables:
        node_id = _make_entity_id(table.entity_type, table.table_name)
        if node_id in seen_ids:
            continue
        seen_ids.add(node_id)
        nodes.append(
            NodeModel(
                id=node_id,
                type=table.entity_type or "unknown",
                label=table.label or table.table_name.replace("_", " ").title(),
                properties={
                    "domain": table.domain,
                    "description": table.description,
                    "column_count": len(table.columns),
                    "synonyms": table.synonyms,
                    "source": "ontology_engine",
                },
            )
        )

    # --- Nodes from taxonomy (may introduce hierarchy nodes) ---
    for tnode in taxonomy_result.hierarchies:
        if tnode.entity_id in seen_ids:
            continue
        seen_ids.add(tnode.entity_id)
        nodes.append(
            NodeModel(
                id=tnode.entity_id,
                type=tnode.entity_type,
                label=tnode.label,
                properties={
                    "taxonomy_level": tnode.level,
                    "source": "ontology_engine",
                },
            )
        )

    # --- Taxonomy edges (BELONGS_TO / parent-child) ---
    for tnode in taxonomy_result.hierarchies:
        if tnode.parent_id and tnode.parent_id in seen_ids:
            edges.append(
                EdgeModel(
                    source=tnode.entity_id,
                    target=tnode.parent_id,
                    type="BELONGS_TO",
                    properties={"source_evidence": "taxonomy_hierarchy"},
                )
            )

    # --- Relationship edges ---
    dropped_count = 0
    for rel in relationship_result.relationships:
        # Only add if both endpoints exist
        if rel.source_id in seen_ids and rel.target_id in seen_ids:
            edges.append(
                EdgeModel(
                    source=rel.source_id,
                    target=rel.target_id,
                    type=rel.relationship_type,
                    properties={
                        **rel.properties,
                        "source_evidence": rel.source_evidence,
                    },
                )
            )
        else:
            dropped_count += 1

    if dropped_count:
        logger.warning(
            "Dropped %d relationships due to missing endpoint nodes", dropped_count
        )

    # --- Optionally merge with sample ontology ---
    if include_sample:
        nodes, edges = _merge_sample_ontology(nodes, edges, seen_ids)

    now = datetime.now(timezone.utc).isoformat()
    return GraphResponse(
        nodes=nodes,
        edges=edges,
        metadata=GraphMetadata(
            total_nodes=len(nodes),
            total_edges=len(edges),
            ontology_version="auto-constructed",
            last_updated=now,
        ),
    )


def _make_entity_id(entity_type: str, table_name: str) -> str:
    """Generate a consistent entity ID from type + table name."""
    prefix_map = {
        "equipment": "equip",
        "products": "prod",
        "orders": "ord",
        "suppliers": "supp",
        "quality": "qual",
        "people": "person",
        "production_lines": "line",
        "materials": "mat",
        "maintenance": "maint",
        "logistics": "logis",
        "safety": "safety",
        "organizational": "org",
    }
    prefix = prefix_map.get(entity_type, entity_type[:4] if entity_type else "ent")
    slug = re.sub(r"[^a-z0-9]+", "-", table_name.lower()).strip("-")
    return f"{prefix}-{slug}"


def _merge_sample_ontology(
    nodes: list[NodeModel],
    edges: list[EdgeModel],
    seen_ids: set[str],
) -> tuple[list[NodeModel], list[EdgeModel]]:
    """Merge existing sample_ontology.json nodes/edges."""
    from pathlib import Path

    sample_path = Path(__file__).parent.parent / "data" / "sample_ontology.json"
    if not sample_path.exists():
        return nodes, edges

    try:
        raw = json.loads(sample_path.read_text())
    except (json.JSONDecodeError, OSError):
        return nodes, edges

    for n in raw.get("nodes", []):
        if n["id"] not in seen_ids:
            seen_ids.add(n["id"])
            nodes.append(NodeModel(**n))

    node_id_set = seen_ids  # all known IDs
    for e in raw.get("edges", []):
        if e["source"] in node_id_set and e["target"] in node_id_set:
            edges.append(EdgeModel(**e))

    return nodes, edges


# ---------------------------------------------------------------------------
# Main construction pipeline (yields SSE events)
# ---------------------------------------------------------------------------

async def construct_ontology(
    document_ids: list[str] | None = None,
    include_sample: bool = False,
) -> AsyncGenerator[OntologySSEEvent, None]:
    """Run the full 4-phase ontology construction pipeline.

    Yields OntologySSEEvent objects that the API route serializes as SSE.
    At the end, updates the in-memory graph store.
    """
    global _construction_status
    _construction_status = OntologyConstructStatus(status="running")

    try:
        # ── Gather schema content from documents ──
        from services.document_manager import document_manager

        if document_ids:
            docs = [
                document_manager.get_document(did)
                for did in document_ids
            ]
            docs = [d for d in docs if d is not None]
        else:
            # Use all reference schema docs + any schema-like sample docs
            all_docs = document_manager.list_documents()
            docs = [
                d
                for d in all_docs
                if d.filename.endswith((".sql", ".csv", ".json", ".md"))
            ]

        if not docs:
            _construction_status.status = "error"
            _construction_status.error_message = "No schema documents found"
            _construction_status.current_phase = None
            yield OntologySSEEvent(
                event="error",
                data={"message": "No schema documents found to analyze"},
            )
            return

        # Collect all schema content as individual parts (for chunking)
        schema_parts: list[str] = []
        for doc in docs:
            content = document_manager.get_document_content(doc.id)
            if content:
                schema_parts.append(
                    f"--- Document: {doc.filename} (type: {doc.filename.rsplit('.', 1)[-1]}) ---\n"
                    f"{content}\n"
                )

        total_chars = sum(len(p) for p in schema_parts)
        chunks_needed = len(_split_schema_into_chunks(schema_parts))

        yield OntologySSEEvent(
            event="construction_start",
            data={
                "documents": [d.filename for d in docs],
                "total_documents": len(docs),
                "total_chars": total_chars,
                "chunks_needed": chunks_needed,
            },
        )

        # ── Phase 1: Schema Analysis + Controlled Vocabulary ──
        _construction_status.current_phase = ConstructionPhase.SCHEMA_ANALYSIS
        yield OntologySSEEvent(
            event="phase_start",
            phase="schema_analysis",
            data={
                "message": f"Analyzing schemas and building controlled vocabulary ({chunks_needed} chunk{'s' if chunks_needed > 1 else ''})...",
            },
        )

        schema_result = await _phase1_chunked(schema_parts)
        entity_id_map = _build_entity_id_map(schema_result.tables)

        _construction_status.total_entities = len(schema_result.tables)

        # Emit each discovered entity
        for table in schema_result.tables:
            yield OntologySSEEvent(
                event="entity_discovered",
                phase="schema_analysis",
                data={
                    "entity_type": table.entity_type,
                    "label": table.label,
                    "domain": table.domain,
                    "table_name": table.table_name,
                    "column_count": len(table.columns),
                },
            )
            await asyncio.sleep(0.02)  # Small delay for streaming effect

        yield OntologySSEEvent(
            event="phase_complete",
            phase="schema_analysis",
            data={
                "entities_found": len(schema_result.tables),
                "domains": schema_result.domains_found,
                "vocabulary_terms": len(schema_result.vocabulary),
            },
        )
        _construction_status.phases_completed.append(ConstructionPhase.SCHEMA_ANALYSIS)

        # ── Phase 2: Taxonomy Construction ──
        _construction_status.current_phase = ConstructionPhase.TAXONOMY
        yield OntologySSEEvent(
            event="phase_start",
            phase="taxonomy",
            data={"message": "Building taxonomic hierarchies..."},
        )

        taxonomy_result = await _phase2_taxonomy(schema_result, entity_id_map)

        _construction_status.total_taxonomy_nodes = len(taxonomy_result.hierarchies)

        for tnode in taxonomy_result.hierarchies:
            yield OntologySSEEvent(
                event="taxonomy_node",
                phase="taxonomy",
                data={
                    "entity_id": tnode.entity_id,
                    "label": tnode.label,
                    "entity_type": tnode.entity_type,
                    "parent_id": tnode.parent_id,
                    "level": tnode.level,
                },
            )
            await asyncio.sleep(0.02)

        yield OntologySSEEvent(
            event="phase_complete",
            phase="taxonomy",
            data={
                "hierarchy_nodes": len(taxonomy_result.hierarchies),
                "hierarchy_types": taxonomy_result.hierarchy_types,
            },
        )
        _construction_status.phases_completed.append(ConstructionPhase.TAXONOMY)

        # ── Phase 3: Relationship Discovery ──
        _construction_status.current_phase = ConstructionPhase.RELATIONSHIPS
        yield OntologySSEEvent(
            event="phase_start",
            phase="relationships",
            data={"message": "Discovering semantic relationships..."},
        )

        relationship_result = await _phase3_relationships(
            schema_result, taxonomy_result, entity_id_map
        )

        _construction_status.total_relationships = len(relationship_result.relationships)

        for rel in relationship_result.relationships:
            yield OntologySSEEvent(
                event="relationship_found",
                phase="relationships",
                data={
                    "source_id": rel.source_id,
                    "target_id": rel.target_id,
                    "type": rel.relationship_type,
                    "evidence": rel.source_evidence,
                },
            )
            await asyncio.sleep(0.02)

        yield OntologySSEEvent(
            event="phase_complete",
            phase="relationships",
            data={
                "relationships_found": len(relationship_result.relationships),
                "types": relationship_result.relationship_types_found,
            },
        )
        _construction_status.phases_completed.append(ConstructionPhase.RELATIONSHIPS)

        # ── Phase 4: Graph Assembly ──
        _construction_status.current_phase = ConstructionPhase.GRAPH_ASSEMBLY
        yield OntologySSEEvent(
            event="phase_start",
            phase="graph_assembly",
            data={"message": "Assembling knowledge graph..."},
        )

        graph = _phase4_assemble_graph(
            schema_result, taxonomy_result, relationship_result, include_sample
        )

        # Update in-memory graph store
        from services.graph_manager import graph_manager

        graph_manager.update_graph(graph)
        graph_manager.save_baseline()
        graph_manager.save_to_disk()
        logger.info(
            "Ontology constructed: %d nodes, %d edges (persisted to disk)",
            len(graph.nodes),
            len(graph.edges),
        )

        # Persist to Neo4j if enabled (non-fatal — in-memory graph is source of truth)
        if settings.neo4j_enabled:
            try:
                await _persist_to_neo4j(graph)
            except Exception as e:
                logger.error("Failed to persist ontology to Neo4j (continuing): %s", e)

        yield OntologySSEEvent(
            event="phase_complete",
            phase="graph_assembly",
            data={
                "total_nodes": len(graph.nodes),
                "total_edges": len(graph.edges),
            },
        )
        _construction_status.phases_completed.append(ConstructionPhase.GRAPH_ASSEMBLY)

        # ── Done ──
        _construction_status.status = "completed"
        _construction_status.current_phase = None
        yield OntologySSEEvent(
            event="construction_complete",
            data={
                "total_nodes": len(graph.nodes),
                "total_edges": len(graph.edges),
                "domains": schema_result.domains_found,
                "relationship_types": relationship_result.relationship_types_found,
            },
        )

    except Exception as e:
        logger.error("Ontology construction failed: %s", e, exc_info=True)
        _construction_status.status = "error"
        _construction_status.error_message = str(e)
        yield OntologySSEEvent(
            event="error",
            data={"message": str(e)},
        )


# ---------------------------------------------------------------------------
# Neo4j persistence
# ---------------------------------------------------------------------------

async def _persist_to_neo4j(graph: GraphResponse) -> None:
    """Write constructed ontology nodes and edges to Neo4j."""
    from services.neo4j_connection import get_driver

    driver = await get_driver()
    label_map = {
        "equipment": "Equipment",
        "products": "Product",
        "orders": "Order",
        "suppliers": "Supplier",
        "quality": "Quality",
        "people": "Person",
        "production_lines": "ProductionLine",
        "materials": "Material",
        "maintenance": "Maintenance",
        "logistics": "Logistics",
        "safety": "Safety",
        "organizational": "Organization",
    }

    async with driver.session() as session:
        # Create nodes
        for node in graph.nodes:
            neo4j_label = label_map.get(node.type, "Entity")
            await session.run(
                f"""
                MERGE (n:{neo4j_label} {{id: $id}})
                SET n.type = $type,
                    n.label = $label,
                    n += $props
                """,
                {
                    "id": node.id,
                    "type": node.type,
                    "label": node.label,
                    "props": {
                        k: (json.dumps(v) if isinstance(v, (list, dict)) else v)
                        for k, v in node.properties.items()
                    },
                },
            )

        # Create relationships
        for edge in graph.edges:
            rel_type = re.sub(r"[^A-Z_]", "_", edge.type.upper())
            await session.run(
                f"""
                MATCH (a {{id: $source}}), (b {{id: $target}})
                MERGE (a)-[r:{rel_type}]->(b)
                SET r += $props
                """,
                {
                    "source": edge.source,
                    "target": edge.target,
                    "props": {
                        k: (json.dumps(v) if isinstance(v, (list, dict)) else v)
                        for k, v in edge.properties.items()
                    },
                },
            )

    logger.info("Persisted ontology to Neo4j: %d nodes, %d edges", len(graph.nodes), len(graph.edges))
