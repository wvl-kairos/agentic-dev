from __future__ import annotations

from pydantic import BaseModel


class ExtractedEntity(BaseModel):
    name: str
    entity_type: str = ""
    matched_node_id: str | None = None
    similarity_score: float = 0.0


class IngestionResult(BaseModel):
    document_id: str
    status: str  # pending | processing | completed | error
    entities_extracted: int = 0
    entities_resolved: int = 0
    edges_created: int = 0
    nodes_created: int = 0
    graph_total_nodes: int = 0
    graph_total_edges: int = 0
    error_message: str | None = None
    extracted_entities: list[ExtractedEntity] = []


class IngestionStatusResponse(BaseModel):
    document_id: str
    status: str
    result: IngestionResult | None = None
