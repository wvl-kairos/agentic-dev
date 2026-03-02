"""Pydantic models for ontology construction pipeline.

Inspired by the Ontology Pipeline framework (Jessica Talisman):
  Controlled Vocabulary → Metadata Standards → Taxonomy → Thesaurus → Ontology → Knowledge Graph

We compress this into 4 practical phases:
  Phase 1: Schema Analysis + Controlled Vocabulary
  Phase 2: Taxonomy Construction
  Phase 3: Relationship Discovery (Thesaurus + Ontology)
  Phase 4: Graph Assembly
"""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Construction phases
# ---------------------------------------------------------------------------

class ConstructionPhase(str, Enum):
    SCHEMA_ANALYSIS = "schema_analysis"
    TAXONOMY = "taxonomy"
    RELATIONSHIPS = "relationships"
    GRAPH_ASSEMBLY = "graph_assembly"


# ---------------------------------------------------------------------------
# Phase 1: Schema Analysis + Controlled Vocabulary
# ---------------------------------------------------------------------------

class ColumnInfo(BaseModel):
    """Column extracted from a schema table."""
    name: str
    data_type: str = ""
    nullable: bool = True
    is_primary_key: bool = False
    is_foreign_key: bool = False
    references_table: str = ""
    references_column: str = ""
    description: str = ""


class TableEntity(BaseModel):
    """A table/entity extracted from schema analysis."""
    table_name: str
    entity_type: str = ""  # equipment, product, order, supplier, etc.
    label: str = ""  # Human-readable display name
    description: str = ""
    domain: str = ""  # production, quality, supply_chain, maintenance, etc.
    columns: list[ColumnInfo] = Field(default_factory=list)
    synonyms: list[str] = Field(default_factory=list)  # Controlled vocabulary


class SchemaAnalysisResult(BaseModel):
    """Output of Phase 1: parsed tables with controlled vocabulary."""
    tables: list[TableEntity] = Field(default_factory=list)
    domains_found: list[str] = Field(default_factory=list)
    vocabulary: dict[str, str] = Field(default_factory=dict)  # term → canonical form


# ---------------------------------------------------------------------------
# Phase 2: Taxonomy
# ---------------------------------------------------------------------------

class TaxonomyNode(BaseModel):
    """A node in the taxonomy hierarchy (broader/narrower terms)."""
    entity_id: str
    label: str
    entity_type: str
    parent_id: str = ""  # broader term
    children_ids: list[str] = Field(default_factory=list)  # narrower terms
    level: int = 0  # depth in hierarchy


class TaxonomyResult(BaseModel):
    """Output of Phase 2: hierarchical taxonomy."""
    hierarchies: list[TaxonomyNode] = Field(default_factory=list)
    hierarchy_types: list[str] = Field(default_factory=list)  # e.g. ["equipment", "product", "organizational"]


# ---------------------------------------------------------------------------
# Phase 3: Relationship Discovery
# ---------------------------------------------------------------------------

class OntologyRelationship(BaseModel):
    """A typed relationship between two entities."""
    source_id: str
    target_id: str
    relationship_type: str  # PRODUCES, REQUIRES, INSPECTED_BY, etc.
    properties: dict[str, Any] = Field(default_factory=dict)
    source_evidence: str = ""  # FK, semantic, domain rule


class RelationshipResult(BaseModel):
    """Output of Phase 3: discovered relationships."""
    relationships: list[OntologyRelationship] = Field(default_factory=list)
    relationship_types_found: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Phase 4: Graph Assembly (uses existing GraphResponse from graph_models.py)
# ---------------------------------------------------------------------------

class OntologyEntity(BaseModel):
    """Final assembled entity ready for graph insertion."""
    id: str
    type: str
    label: str
    domain: str = ""
    properties: dict[str, Any] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# API models
# ---------------------------------------------------------------------------

class OntologyConstructRequest(BaseModel):
    """Request to construct ontology from uploaded/existing documents."""
    document_ids: list[str] = Field(
        default_factory=list,
        description="Document IDs to analyze. If empty, uses all reference schema docs.",
    )
    include_sample_ontology: bool = Field(
        default=False,
        description="Merge with existing sample_ontology.json data.",
    )


class OntologyConstructStatus(BaseModel):
    """Status of an ongoing or completed construction."""
    status: str = "idle"  # idle, running, completed, error
    current_phase: ConstructionPhase | None = None
    phases_completed: list[ConstructionPhase] = Field(default_factory=list)
    total_entities: int = 0
    total_relationships: int = 0
    total_taxonomy_nodes: int = 0
    error_message: str = ""


# ---------------------------------------------------------------------------
# SSE event models
# ---------------------------------------------------------------------------

class OntologySSEEvent(BaseModel):
    """Server-Sent Event for ontology construction streaming."""
    event: str  # phase_start, entity_discovered, relationship_found, phase_complete, etc.
    phase: str = ""
    data: dict[str, Any] = Field(default_factory=dict)
