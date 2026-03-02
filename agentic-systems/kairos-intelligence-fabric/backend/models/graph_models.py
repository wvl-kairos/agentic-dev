from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class NodeModel(BaseModel):
    id: str
    type: str
    label: str
    properties: dict[str, Any] = Field(default_factory=dict)
    position: list[float] | None = None


class EdgeModel(BaseModel):
    source: str
    target: str
    type: str
    properties: dict[str, Any] = Field(default_factory=dict)


class GraphMetadata(BaseModel):
    total_nodes: int
    total_edges: int
    ontology_version: str
    last_updated: str


class GraphResponse(BaseModel):
    nodes: list[NodeModel]
    edges: list[EdgeModel]
    metadata: GraphMetadata
