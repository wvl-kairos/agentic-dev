from __future__ import annotations

from models.query_models import RetrievalContext, SourceAttribution


def merge_contexts(
    graph_context: str,
    graph_sources: list[SourceAttribution],
    rag_context: str,
    rag_sources: list[SourceAttribution],
) -> RetrievalContext:
    """Merge graph and RAG retrieval results into unified context."""

    # Deduplicate sources by id
    seen_ids: set[str] = set()
    all_sources: list[SourceAttribution] = []

    for source in graph_sources + rag_sources:
        if source.id not in seen_ids:
            seen_ids.add(source.id)
            all_sources.append(source)

    # Sort by relevance descending
    all_sources.sort(key=lambda s: s.relevance, reverse=True)

    return RetrievalContext(
        graph_context=graph_context,
        rag_context=rag_context,
        sources=all_sources[:15],
    )


def format_context_for_llm(context: RetrievalContext) -> str:
    """Format retrieval context into a string suitable for LLM consumption."""
    parts: list[str] = []

    if context.graph_context:
        parts.append("=== GRAPH KNOWLEDGE ===")
        parts.append(context.graph_context)

    if context.rag_context:
        parts.append("\n=== DOCUMENT KNOWLEDGE (Multi-hop RAG) ===")
        parts.append(context.rag_context)

    if not parts:
        return "No relevant context found."

    return "\n".join(parts)
