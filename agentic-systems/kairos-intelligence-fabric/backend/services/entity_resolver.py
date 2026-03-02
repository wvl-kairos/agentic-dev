from __future__ import annotations

import logging

from models.graph_models import NodeModel
from services.embedding_service import cosine_similarity, get_embedding, get_embeddings_batch

logger = logging.getLogger(__name__)

SIMILARITY_THRESHOLD = 0.80


class EntityResolver:
    """Matches LightRAG-extracted entity names to existing ontology nodes."""

    def __init__(self, ontology_nodes: list[NodeModel]) -> None:
        self._nodes = ontology_nodes
        self._node_labels = [n.label for n in ontology_nodes]
        self._node_embeddings: list[list[float]] | None = None

    async def _ensure_embeddings(self) -> None:
        if self._node_embeddings is None:
            logger.info("Computing embeddings for %d ontology nodes", len(self._node_labels))
            self._node_embeddings = await get_embeddings_batch(self._node_labels)

    async def resolve(self, entity_name: str) -> list[tuple[NodeModel, float]]:
        """Find ontology nodes matching the entity name.

        Returns list of (node, similarity_score) tuples above threshold,
        sorted by score descending.
        """
        await self._ensure_embeddings()
        assert self._node_embeddings is not None

        entity_emb = await get_embedding(entity_name)
        matches: list[tuple[NodeModel, float]] = []

        for node, node_emb in zip(self._nodes, self._node_embeddings):
            score = cosine_similarity(entity_emb, node_emb)
            if score >= SIMILARITY_THRESHOLD:
                matches.append((node, score))

        # Also do exact/fuzzy string match as a fast path
        entity_lower = entity_name.lower().strip()
        for node in self._nodes:
            label_lower = node.label.lower().strip()
            # Exact match
            if entity_lower == label_lower:
                if not any(m[0].id == node.id for m in matches):
                    matches.append((node, 1.0))
            # Substring match (entity contained in label or vice versa)
            elif entity_lower in label_lower or label_lower in entity_lower:
                if not any(m[0].id == node.id for m in matches):
                    matches.append((node, 0.90))

        matches.sort(key=lambda x: x[1], reverse=True)
        return matches
