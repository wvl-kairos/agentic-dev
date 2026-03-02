from __future__ import annotations

import logging
import re
from typing import Any

from config import settings
from models.query_models import SourceAttribution

logger = logging.getLogger(__name__)


async def retrieve_from_graph(query: str) -> tuple[str, list[SourceAttribution]]:
    """Retrieve relevant context from the graph based on the query.

    Returns (context_string, source_attributions).
    """
    if not settings.neo4j_enabled:
        return await _retrieve_from_memory(query)

    return await _retrieve_from_neo4j(query)


async def _retrieve_from_memory(query: str) -> tuple[str, list[SourceAttribution]]:
    """Fallback: search in-memory graph."""
    from services.graph_manager import graph_manager

    graph = graph_manager.get_graph()
    q_lower = query.lower()
    sources: list[SourceAttribution] = []
    context_parts: list[str] = []

    # Find matching nodes
    for node in graph.nodes:
        if node.label.lower() in q_lower or any(
            word in node.label.lower() for word in q_lower.split() if len(word) > 3
        ):
            context_parts.append(
                f"Node: {node.label} (type: {node.type}, id: {node.id})\n"
                f"  Properties: {node.properties}"
            )
            sources.append(SourceAttribution(
                type="graph", id=node.id, label=node.label, relevance=0.9,
            ))

            # Get connected edges
            for edge in graph.edges:
                if edge.source == node.id or edge.target == node.id:
                    other_id = edge.target if edge.source == node.id else edge.source
                    other_node = next((n for n in graph.nodes if n.id == other_id), None)
                    if other_node:
                        context_parts.append(
                            f"  -> {edge.type} -> {other_node.label} ({other_node.type})"
                        )

    if not context_parts:
        return "", []

    return "\n".join(context_parts[:20]), sources[:10]


async def _retrieve_from_neo4j(query: str) -> tuple[str, list[SourceAttribution]]:
    """Search Neo4j for relevant nodes and their neighborhoods."""
    from services.neo4j_connection import get_driver

    driver = await get_driver()
    sources: list[SourceAttribution] = []
    context_parts: list[str] = []

    # Extract potential entity names from query
    words = [w for w in query.split() if len(w) > 2]

    async with driver.session() as session:
        # Search by label or properties containing query terms
        for word in words:
            result = await session.run(
                """
                MATCH (n)
                WHERE toLower(n.label) CONTAINS $term_lower OR n.id CONTAINS $term_lower
                RETURN n.id AS id, n.label AS label, n.type AS type, properties(n) AS props
                LIMIT 5
                """,
                {"term_lower": word.lower()},
            )
            async for record in result:
                node_id = record["id"]
                if any(s.id == node_id for s in sources):
                    continue

                label = record["label"] or node_id
                props = record["props"] or {}
                context_parts.append(f"Node: {label} (type: {record['type']}, id: {node_id})")

                # Filter out internal props for context
                display_props = {k: v for k, v in props.items() if k not in ("id", "label", "type")}
                if display_props:
                    context_parts.append(f"  Properties: {display_props}")

                sources.append(SourceAttribution(
                    type="graph", id=node_id, label=label, relevance=0.9,
                ))

                # Get neighborhood
                neighbors_result = await session.run(
                    """
                    MATCH (n {id: $nid})-[r]-(m)
                    RETURN type(r) AS rel, m.label AS label, m.type AS type, m.id AS mid
                    LIMIT 10
                    """,
                    {"nid": node_id},
                )
                async for nrec in neighbors_result:
                    context_parts.append(
                        f"  -- {nrec['rel']} --> {nrec['label']} ({nrec['type']})"
                    )

    return "\n".join(context_parts[:30]), sources[:10]
