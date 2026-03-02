from __future__ import annotations

import asyncio
import json
import logging
from dataclasses import dataclass, field

import anthropic

from config import settings
from services.hybrid_retriever import hybrid_retrieve

logger = logging.getLogger(__name__)

# Singleton Anthropic client (avoids connection leaks)
_anthropic_client: anthropic.AsyncAnthropic | None = None


def _get_anthropic_client() -> anthropic.AsyncAnthropic:
    global _anthropic_client
    if _anthropic_client is None:
        _anthropic_client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
    return _anthropic_client


@dataclass
class HopTrace:
    hop: int
    query: str
    chunk_count: int


@dataclass
class MultiHopResult:
    context_text: str
    sources: list[dict]
    hops: list[HopTrace] = field(default_factory=list)
    is_multihop: bool = False


async def multihop_retrieve(
    query: str,
    top_k: int | None = None,
) -> MultiHopResult:
    """2-hop agentic retrieval with Chain of Thought bridging.

    Hop 1: hybrid_retrieve(original query)
    Claude CoT: decide if context is sufficient; if not, generate bridging query
    Hop 2 (conditional): hybrid_retrieve(bridging query)
    Merge + deduplicate
    """
    if top_k is None:
        top_k = settings.rag_top_k

    # --- Hop 1 (offload sync call to thread pool) ---
    hop1_chunks = await asyncio.to_thread(hybrid_retrieve, query, top_k)
    hop1_trace = HopTrace(hop=1, query=query, chunk_count=len(hop1_chunks))
    logger.info("Hop 1: query=%r, chunks=%d", query, len(hop1_chunks))

    if not hop1_chunks:
        return MultiHopResult(
            context_text="",
            sources=[],
            hops=[hop1_trace],
        )

    hop1_context = _format_chunks(hop1_chunks)

    # --- CoT: decide if hop 2 is needed ---
    bridging_query = await _generate_bridging_query(query, hop1_context)

    if bridging_query is None:
        # Context is sufficient — single hop
        return MultiHopResult(
            context_text=hop1_context,
            sources=_extract_sources(hop1_chunks),
            hops=[hop1_trace],
            is_multihop=False,
        )

    # --- Hop 2 (offload sync call to thread pool) ---
    hop2_chunks = await asyncio.to_thread(hybrid_retrieve, bridging_query, top_k)
    hop2_trace = HopTrace(hop=2, query=bridging_query, chunk_count=len(hop2_chunks))
    logger.info("Hop 2: bridging query=%r, chunks=%d", bridging_query, len(hop2_chunks))

    # Merge + deduplicate
    merged = _merge_and_deduplicate(hop1_chunks, hop2_chunks)
    merged_context = _format_chunks(merged)

    return MultiHopResult(
        context_text=merged_context,
        sources=_extract_sources(merged),
        hops=[hop1_trace, hop2_trace],
        is_multihop=True,
    )


async def _generate_bridging_query(
    original_query: str,
    hop1_context: str,
) -> str | None:
    """Use Claude to decide if hop 2 is needed and generate a bridging query.

    Returns the bridging query string, or None if context is sufficient.
    """
    try:
        client = _get_anthropic_client()

        # Defensive truncation of user query in prompt
        safe_query = original_query[:1000]

        response = await client.messages.create(
            model=settings.agent_model,
            max_tokens=256,
            temperature=0.0,
            messages=[
                {
                    "role": "user",
                    "content": f"""You are a retrieval agent for a manufacturing knowledge base. Given a user query and retrieved context, decide if the context is sufficient to answer the query fully.

User query: {safe_query}

Retrieved context:
{hop1_context[:3000]}

Respond with ONLY valid JSON (no markdown, no explanation):
{{"sufficient": true/false, "bridging_query": "follow-up search query if not sufficient, else empty string", "reasoning": "brief explanation"}}

Examples of when context is NOT sufficient:
- Query asks about equipment maintenance but context only has equipment IDs/names without procedures
- Query asks about supplier quality but context only mentions supplier names without quality data
- Query connects two concepts (e.g., "equipment that produces X") but context only has one side

Generate a bridging query that retrieves the MISSING information.""",
                }
            ],
        )

        text = response.content[0].text.strip()
        parsed = json.loads(text)

        if not isinstance(parsed, dict):
            logger.warning("CoT: expected dict, got %s", type(parsed).__name__)
            return None

        if parsed.get("sufficient", True):
            logger.info("CoT: context sufficient — single hop")
            return None

        bridging = parsed.get("bridging_query", "")
        if not isinstance(bridging, str):
            bridging = ""
        bridging = bridging.strip()[:500]
        if not bridging:
            return None

        logger.info("CoT: bridging needed — reason=%r, query=%r", parsed.get("reasoning", ""), bridging)
        return bridging

    except Exception as e:
        logger.warning("Bridging query generation failed: %s — falling back to single hop", e)
        return None


def _format_chunks(chunks: list[dict]) -> str:
    """Format chunks into a context string for the LLM."""
    parts: list[str] = []
    for chunk in chunks:
        meta = chunk.get("metadata", {})
        title = meta.get("document_title", "Unknown")
        section = meta.get("section_title", "")
        header = f"[{title}]"
        if section:
            header += f" — {section}"
        parts.append(f"{header}\n{chunk.get('text', '')}")
    return "\n\n---\n\n".join(parts)


def _extract_sources(chunks: list[dict]) -> list[dict]:
    """Extract unique source attributions from chunks."""
    seen: set[str] = set()
    sources: list[dict] = []
    for chunk in chunks:
        meta = chunk.get("metadata", {})
        doc_id = meta.get("document_id", "")
        if doc_id and doc_id not in seen:
            seen.add(doc_id)
            sources.append({
                "type": "document",
                "id": doc_id,
                "label": meta.get("document_title", doc_id),
                "relevance": chunk.get("rrf_score", 0.5),
            })
    return sources


def _merge_and_deduplicate(hop1: list[dict], hop2: list[dict]) -> list[dict]:
    """Merge two hop results, deduplicating by chunk_id."""
    seen: set[str] = set()
    merged: list[dict] = []
    for chunk in hop1 + hop2:
        cid = chunk.get("chunk_id", "")
        if cid not in seen:
            seen.add(cid)
            merged.append(chunk)
    return merged
