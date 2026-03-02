from __future__ import annotations

import logging

from config import settings
from models.query_models import SourceAttribution

logger = logging.getLogger(__name__)


async def retrieve_from_rag(query: str, mode: str = "hybrid") -> tuple[str, list[SourceAttribution]]:
    """Multi-hop agentic RAG retrieval with Chain of Thought.

    Drop-in replacement — same signature as the original LightRAG-based retriever.
    Returns (context_string, source_attributions).
    """
    if not settings.openai_api_key:
        logger.warning("OpenAI API key not set — skipping RAG retrieval")
        return "", []

    try:
        from services.multihop_rag import multihop_retrieve

        result = await multihop_retrieve(query)

        if not result.context_text:
            return "", []

        sources = [
            SourceAttribution(
                type=s.get("type", "document"),
                id=s.get("id", "unknown"),
                label=s.get("label", "Document"),
                relevance=min(float(s.get("relevance", 0.5)), 1.0),
            )
            for s in result.sources
        ]

        hop_info = " → ".join(
            f"hop{h.hop}({h.chunk_count} chunks)" for h in result.hops
        )
        logger.info("RAG retrieval: %s, multihop=%s", hop_info, result.is_multihop)

        return result.context_text, sources

    except Exception as e:
        logger.error("RAG retrieval failed: %s", e)
        return "", []
