from __future__ import annotations

from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    query: str
    mode: str = "hybrid"  # graph_lookup | document_search | hybrid | analytical


class SourceAttribution(BaseModel):
    type: str  # graph | document | knowledge
    id: str
    label: str
    relevance: float = 1.0


class RetrievalContext(BaseModel):
    graph_context: str = ""
    rag_context: str = ""
    sources: list[SourceAttribution] = []


class QueryResponse(BaseModel):
    response: str
    query: str
    mode: str
    sources: list[SourceAttribution] = []
    context: RetrievalContext | None = None
