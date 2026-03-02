from __future__ import annotations

import asyncio
import logging
from typing import Any

from services.document_manager import document_manager

logger = logging.getLogger(__name__)

DOCUMENT_TOOLS = [
    {
        "name": "search_documents",
        "description": "Search documents using hybrid retrieval (semantic + keyword). Returns relevant document chunks with entity references.",
        "input_schema": {
            "type": "object",
            "properties": {
                "search_term": {
                    "type": "string",
                    "description": "The term to search for across document content",
                }
            },
            "required": ["search_term"],
        },
    },
    {
        "name": "get_document_content",
        "description": "Get the full text content of a specific document by its ID.",
        "input_schema": {
            "type": "object",
            "properties": {
                "document_id": {
                    "type": "string",
                    "description": "The ID of the document to retrieve",
                }
            },
            "required": ["document_id"],
        },
    },
]


async def search_documents(search_term: str) -> list[dict[str, Any]]:
    # Try hybrid retrieval first (BM25 + dense vectors)
    try:
        from services.hybrid_retriever import hybrid_retrieve
        chunks = await asyncio.to_thread(hybrid_retrieve, search_term, 5)
        if chunks:
            results = []
            seen_docs: set[str] = set()
            for chunk in chunks:
                meta = chunk.get("metadata", {})
                doc_id = meta.get("document_id", "")
                if doc_id and doc_id not in seen_docs:
                    seen_docs.add(doc_id)
                    entity_str = meta.get("entity_ids", "")
                    results.append({
                        "document_id": doc_id,
                        "document_title": meta.get("document_title", ""),
                        "section": meta.get("section_title", ""),
                        "text": chunk.get("text", "")[:500],
                        "relevance": chunk.get("rrf_score", 0.0),
                        "entity_ids": entity_str.split(",") if entity_str else [],
                    })
            return results
    except Exception as exc:
        logger.warning("hybrid_retrieve failed for search_term=%r, falling back to title search: %s", search_term, exc)

    # Fallback to title search if vector store is empty or unavailable
    docs = document_manager.list_documents()
    term_lower = search_term.lower()
    results = []
    for doc in docs:
        if term_lower in doc.title.lower() or term_lower in doc.filename.lower():
            results.append({
                "document_id": doc.id,
                "document_title": doc.title,
                "section": "",
                "text": doc.content_preview[:500],
                "relevance": 0.5,
                "entity_ids": [],
            })
    return results[:10]


async def get_document_content(document_id: str) -> dict[str, Any]:
    content = document_manager.get_document_content(document_id)
    if content is None:
        return {"error": "Document not found"}
    doc = document_manager.get_document(document_id)
    return {
        "id": document_id,
        "title": doc.title if doc else document_id,
        "content": content[:8000],  # Limit content length for context window
    }
