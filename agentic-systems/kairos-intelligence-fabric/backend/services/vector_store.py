from __future__ import annotations

import logging
from pathlib import Path

import chromadb
from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction

from config import settings
from services.chunking_service import DocumentChunk

logger = logging.getLogger(__name__)

_client: chromadb.ClientAPI | None = None
_embedding_fn: OpenAIEmbeddingFunction | None = None


def _get_client() -> chromadb.ClientAPI:
    global _client
    if _client is None:
        persist_dir = Path(settings.chromadb_persist_dir)
        persist_dir.mkdir(parents=True, exist_ok=True)
        _client = chromadb.PersistentClient(path=str(persist_dir))
        logger.info("ChromaDB client initialized at %s", persist_dir)
    return _client


def _get_embedding_fn() -> OpenAIEmbeddingFunction:
    global _embedding_fn
    if _embedding_fn is None:
        _embedding_fn = OpenAIEmbeddingFunction(
            api_key=settings.openai_api_key,
            model_name=settings.embedding_model,
        )
    return _embedding_fn


def get_collection() -> chromadb.Collection:
    """Get or create the cerebro_chunks collection."""
    client = _get_client()
    return client.get_or_create_collection(
        name="cerebro_chunks",
        embedding_function=_get_embedding_fn(),
        metadata={"hnsw:space": "cosine"},
    )


_MAX_TOKENS_PER_BATCH = 200_000  # Stay well under OpenAI's 300K token limit
_CHARS_PER_TOKEN = 2.5  # Conservative: structured content has short tokens
_MAX_CHARS_PER_BATCH = int(_MAX_TOKENS_PER_BATCH * _CHARS_PER_TOKEN)  # ~500K chars
_MAX_CHARS_PER_CHUNK = 8_000  # text-embedding-3-small limit is 8192 tokens; structured data ≈ 1.6 chars/token


def _split_oversized(chunks: list[DocumentChunk]) -> list[DocumentChunk]:
    """Split any chunk that exceeds the embedding model's token limit."""
    result: list[DocumentChunk] = []
    for c in chunks:
        if len(c.text) <= _MAX_CHARS_PER_CHUNK:
            result.append(c)
            continue
        # Split into sub-chunks at paragraph or line boundaries
        text = c.text
        part = 0
        while text:
            segment = text[:_MAX_CHARS_PER_CHUNK]
            # Try to cut at a newline boundary
            if len(text) > _MAX_CHARS_PER_CHUNK:
                last_nl = segment.rfind("\n")
                if last_nl > _MAX_CHARS_PER_CHUNK // 2:
                    segment = segment[:last_nl]
            result.append(DocumentChunk(
                chunk_id=f"{c.chunk_id}--p{part}",
                document_id=c.document_id,
                document_title=c.document_title,
                chunk_index=c.chunk_index * 100 + part,
                text=segment,
                section_title=c.section_title,
                entity_ids=c.entity_ids if part == 0 else [],
                source_format=c.source_format,
            ))
            text = text[len(segment):].lstrip()
            part += 1
        logger.info("Split oversized chunk %s (%dK chars) into %d parts", c.chunk_id, len(c.text) // 1000, part)
    return result


def add_chunks(chunks: list[DocumentChunk]) -> int:
    """Upsert document chunks into ChromaDB in token-safe batches. Returns count added."""
    if not chunks:
        return 0

    # Split any oversized chunks before embedding
    chunks = _split_oversized(chunks)

    collection = get_collection()
    total = 0
    batch_num = 0

    # Build batches based on total character count, not fixed chunk count
    batch_ids: list[str] = []
    batch_docs: list[str] = []
    batch_metas: list[dict] = []
    batch_chars = 0

    def _flush() -> None:
        nonlocal total, batch_num, batch_ids, batch_docs, batch_metas, batch_chars
        if not batch_ids:
            return
        batch_num += 1
        logger.info("Upsert batch %d: %d chunks, ~%dK chars", batch_num, len(batch_ids), batch_chars // 1000)
        collection.upsert(ids=batch_ids, documents=batch_docs, metadatas=batch_metas)
        total += len(batch_ids)
        batch_ids, batch_docs, batch_metas, batch_chars = [], [], [], 0

    for c in chunks:
        chunk_len = len(c.text)
        if batch_chars + chunk_len > _MAX_CHARS_PER_BATCH and batch_ids:
            _flush()
        batch_ids.append(c.chunk_id)
        batch_docs.append(c.text)
        batch_metas.append({
            "document_id": c.document_id,
            "document_title": c.document_title,
            "chunk_index": c.chunk_index,
            "section_title": c.section_title,
            "entity_ids": ",".join(c.entity_ids),
            "source_format": c.source_format,
        })
        batch_chars += chunk_len

    _flush()
    logger.info("Upserted %d chunks total into ChromaDB (%d batches)", total, batch_num)
    return total


def query_dense(query: str, n_results: int = 5) -> list[dict]:
    """Semantic similarity search. Returns list of {chunk_id, text, metadata, distance}."""
    collection = get_collection()
    if collection.count() == 0:
        return []

    results = collection.query(
        query_texts=[query],
        n_results=min(n_results, collection.count()),
    )

    items: list[dict] = []
    for i in range(len(results["ids"][0])):
        items.append({
            "chunk_id": results["ids"][0][i],
            "text": results["documents"][0][i],
            "metadata": results["metadatas"][0][i],
            "distance": results["distances"][0][i] if results.get("distances") else 0.0,
        })
    return items


def delete_document_chunks(doc_id: str) -> int:
    """Delete all chunks for a document. Returns count deleted."""
    collection = get_collection()
    existing = collection.get(where={"document_id": doc_id})
    if existing["ids"]:
        collection.delete(ids=existing["ids"])
        logger.info("Deleted %d chunks for document %s", len(existing["ids"]), doc_id)
        return len(existing["ids"])
    return 0


def get_ingested_doc_ids() -> set[str]:
    """Return the set of document IDs that have chunks in ChromaDB."""
    collection = get_collection()
    if collection.count() == 0:
        return set()
    results = collection.get(include=["metadatas"])
    return {m["document_id"] for m in results["metadatas"] if m.get("document_id")}


def get_all_chunks() -> list[dict]:
    """Returns all chunks for BM25 index building."""
    collection = get_collection()
    if collection.count() == 0:
        return []

    results = collection.get(include=["documents", "metadatas"])
    items: list[dict] = []
    for i in range(len(results["ids"])):
        items.append({
            "chunk_id": results["ids"][i],
            "text": results["documents"][i],
            "metadata": results["metadatas"][i],
        })
    return items
