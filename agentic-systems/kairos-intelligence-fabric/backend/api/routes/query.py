from __future__ import annotations

import json
import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from models.query_models import QueryRequest, QueryResponse
from services.context_merger import format_context_for_llm, merge_contexts
from services.graph_retriever import retrieve_from_graph
from services.query_router import classify_query
from services.rag_retriever import retrieve_from_rag
from services.websocket_manager import ws_manager

logger = logging.getLogger(__name__)

router = APIRouter()


async def _process_query(
    query: str,
    history: list[dict[str, str]] | None = None,
) -> QueryResponse:
    """Core query processing: route → retrieve → merge → respond."""
    mode = classify_query(query)
    logger.info("Query classified as: %s", mode)

    # Retrieve from both sources based on mode
    graph_context, graph_sources = "", []
    rag_context, rag_sources = "", []

    if mode in ("graph_lookup", "hybrid", "analytical"):
        graph_context, graph_sources = await retrieve_from_graph(query)

    if mode in ("document_search", "hybrid", "analytical"):
        rag_context, rag_sources = await retrieve_from_rag(query)

    # Merge contexts
    context = merge_contexts(graph_context, graph_sources, rag_context, rag_sources)
    formatted = format_context_for_llm(context)

    # Generate response using agent (or fallback)
    try:
        from agents.orchestrator import process_with_agents

        response_text = await process_with_agents(query, formatted, mode, history=history)
    except (ImportError, Exception) as e:
        logger.warning("Agent processing unavailable, using context directly: %s", e)
        response_text = _format_fallback_response(query, formatted, mode)

    return QueryResponse(
        response=response_text,
        query=query,
        mode=mode,
        sources=context.sources,
        context=context,
    )


def _format_fallback_response(query: str, context: str, mode: str) -> str:
    """Simple fallback when agents are not available."""
    if not context or context == "No relevant context found.":
        return (
            f"I found limited information for your query about '{query}'. "
            "Try uploading relevant documents or refining your question."
        )

    return (
        f"Based on the available {mode} data:\n\n{context}\n\n"
        "Note: Full agent-powered analysis requires API keys to be configured."
    )


@router.post("/query", response_model=QueryResponse)
async def query_endpoint(request: QueryRequest):
    return await _process_query(request.query)


@router.websocket("/ws/chat")
async def websocket_chat(ws: WebSocket):
    await ws_manager.connect(ws)
    try:
        while True:
            data = await ws.receive_text()
            try:
                msg = json.loads(data)
                query = msg.get("query", "")
                history = msg.get("history", [])
            except json.JSONDecodeError:
                query = data
                history = []

            if not query:
                await ws_manager.send_chunk(ws, "error", "Empty query")
                continue

            await ws_manager.send_chunk(ws, "thinking", "Analyzing query...")

            try:
                result = await _process_query(query, history=history or None)

                # Stream the response
                await ws_manager.stream_text(ws, result.response, chunk_size=8)

                # Send sources
                if result.sources:
                    sources_data = [s.model_dump() for s in result.sources]
                    await ws_manager.send_chunk(ws, "source", json.dumps(sources_data))

                await ws_manager.send_chunk(ws, "done", "")

            except Exception as e:
                logger.error("Query processing failed: %s", e)
                await ws_manager.send_chunk(ws, "error", str(e))

    except WebSocketDisconnect:
        ws_manager.disconnect(ws)
