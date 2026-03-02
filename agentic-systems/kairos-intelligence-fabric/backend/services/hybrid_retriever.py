from __future__ import annotations

import logging
import threading
from collections import defaultdict

from rank_bm25 import BM25Okapi

from config import settings
from services.vector_store import query_dense, get_all_chunks

logger = logging.getLogger(__name__)

# Module-level BM25 index (rebuilt on startup and after each ingestion)
_bm25_lock = threading.Lock()
_bm25_index: BM25Okapi | None = None
_bm25_chunks: list[dict] = []
_doc_title_map: dict[str, str] = {}  # doc_id -> title (cached at rebuild time)


def rebuild_bm25_index() -> int:
    """Rebuild the in-memory BM25 index from all ChromaDB chunks.

    Returns the number of chunks indexed.
    """
    global _bm25_index, _bm25_chunks, _doc_title_map

    chunks = get_all_chunks()

    if not chunks:
        with _bm25_lock:
            _bm25_index = None
            _bm25_chunks = []
            _doc_title_map = {}
        logger.info("BM25 index: 0 chunks (empty)")
        return 0

    tokenized = [_tokenize(c["text"]) for c in chunks]
    index = BM25Okapi(tokenized)

    title_map = {}
    for c in chunks:
        meta = c.get("metadata", {})
        did = meta.get("document_id", "")
        title_map[did] = meta.get("document_title", "")

    with _bm25_lock:
        _bm25_chunks = chunks
        _bm25_index = index
        _doc_title_map = title_map

    logger.info("BM25 index rebuilt with %d chunks", len(chunks))
    return len(chunks)


def query_bm25(query: str, top_k: int = 5) -> list[dict]:
    """Sparse keyword search using BM25. Returns ranked chunks."""
    with _bm25_lock:
        index = _bm25_index
        chunks = list(_bm25_chunks)

    if index is None or not chunks:
        return []

    tokens = _tokenize(query)
    scores = index.get_scores(tokens)

    scored = sorted(
        enumerate(scores),
        key=lambda x: x[1],
        reverse=True,
    )[:top_k]

    results: list[dict] = []
    for idx, score in scored:
        if score > 0:
            chunk = chunks[idx].copy()
            chunk["bm25_score"] = float(score)
            results.append(chunk)
    return results


def hybrid_retrieve(
    query: str,
    top_k: int | None = None,
    rrf_k: int | None = None,
) -> list[dict]:
    """Core hybrid retrieval: BM25 + dense + RRF fusion + title-mention expansion.

    Returns list of chunks sorted by fused relevance score.
    """
    if top_k is None:
        top_k = settings.rag_top_k
    if rrf_k is None:
        rrf_k = settings.rag_rrf_k

    # Retrieve from both sources (fetch more candidates for fusion)
    fetch_k = top_k * 3
    bm25_results = query_bm25(query, top_k=fetch_k)
    dense_results = query_dense(query, n_results=fetch_k)

    # RRF fusion
    fused = _reciprocal_rank_fusion(bm25_results, dense_results, k=rrf_k)

    # Title-mention expansion
    expanded = _title_mention_expansion(fused, max_total=top_k + 2)

    return expanded[:top_k]


def _reciprocal_rank_fusion(
    bm25_results: list[dict],
    dense_results: list[dict],
    k: int = 60,
) -> list[dict]:
    """Fuse two ranked lists using Reciprocal Rank Fusion.

    score(d) = sum(weight_i / (k + rank_i))
    """
    scores: dict[str, float] = defaultdict(float)
    chunk_map: dict[str, dict] = {}

    bm25_weight = 0.4
    dense_weight = 0.6

    for rank, chunk in enumerate(bm25_results):
        cid = chunk["chunk_id"]
        scores[cid] += bm25_weight / (k + rank + 1)
        chunk_map[cid] = chunk

    for rank, chunk in enumerate(dense_results):
        cid = chunk["chunk_id"]
        scores[cid] += dense_weight / (k + rank + 1)
        chunk_map[cid] = chunk

    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    results: list[dict] = []
    for cid, score in ranked:
        item = chunk_map[cid].copy()
        item["rrf_score"] = score
        results.append(item)

    return results


def _title_mention_expansion(results: list[dict], max_total: int) -> list[dict]:
    """If a retrieved chunk mentions another document's title, pull in that doc's top chunk.

    Uses cached _bm25_chunks and _doc_title_map (rebuilt at index time) instead of
    querying ChromaDB on every call.
    """
    if not results:
        return results

    with _bm25_lock:
        all_chunks = list(_bm25_chunks)
        doc_title_map = dict(_doc_title_map)

    if not all_chunks:
        return results

    # Collect doc IDs already in results
    seen_doc_ids: set[str] = set()
    for r in results:
        meta = r.get("metadata", {})
        seen_doc_ids.add(meta.get("document_id", ""))

    # Check if any chunk text mentions a title of a doc NOT already in results
    mentioned_doc_ids: set[str] = set()
    for r in results:
        text_lower = r.get("text", "").lower()
        for doc_id, title in doc_title_map.items():
            if doc_id not in seen_doc_ids and title and title.lower() in text_lower:
                mentioned_doc_ids.add(doc_id)

    if not mentioned_doc_ids:
        return results

    # Add the first chunk (chunk_index=0) from each mentioned doc
    expansion: list[dict] = []
    for c in all_chunks:
        meta = c.get("metadata", {})
        if meta.get("document_id") in mentioned_doc_ids and meta.get("chunk_index") == 0:
            item = c.copy()
            item["rrf_score"] = 0.001  # low score, just for context
            expansion.append(item)
            mentioned_doc_ids.discard(meta.get("document_id"))

    return (results + expansion)[:max_total]


def _tokenize(text: str) -> list[str]:
    """Simple whitespace + lowercase tokenization for BM25."""
    return text.lower().split()
