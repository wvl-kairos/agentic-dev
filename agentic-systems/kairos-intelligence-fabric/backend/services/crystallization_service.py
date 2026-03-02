from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone

from config import settings

logger = logging.getLogger(__name__)


async def save_insight(
    content: str,
    related_entity_ids: list[str],
    confidence: float = 0.8,
    agent_name: str = "",
    query: str = "",
) -> dict:
    """Save an agent-generated insight as a Knowledge node in the graph.

    Creates a (:Knowledge) node and links it to related entities via EXTRACTED_FROM edges.
    """
    insight_id = f"knowledge-{uuid.uuid4().hex[:8]}"
    now = datetime.now(timezone.utc).isoformat()

    if settings.neo4j_enabled:
        from services.neo4j_connection import get_driver

        driver = await get_driver()
        async with driver.session() as session:
            # Create knowledge node
            await session.run(
                """
                CREATE (k:Knowledge {
                    id: $id,
                    type: 'knowledge',
                    label: $label,
                    content: $content,
                    confidence: $confidence,
                    agent: $agent,
                    query: $query,
                    created_at: $now
                })
                """,
                {
                    "id": insight_id,
                    "label": content[:60] + "..." if len(content) > 60 else content,
                    "content": content,
                    "confidence": confidence,
                    "agent": agent_name,
                    "query": query,
                    "now": now,
                },
            )

            # Link to related entities
            for entity_id in related_entity_ids:
                await session.run(
                    """
                    MATCH (k:Knowledge {id: $kid}), (n {id: $eid})
                    CREATE (k)-[:EXTRACTED_FROM {created_at: $now}]->(n)
                    """,
                    {"kid": insight_id, "eid": entity_id, "now": now},
                )

        logger.info(
            "Crystallized insight %s linked to %d entities",
            insight_id, len(related_entity_ids),
        )
    else:
        logger.info("Insight saved (in-memory only, no Neo4j): %s", insight_id)

    return {
        "id": insight_id,
        "content": content,
        "confidence": confidence,
        "agent": agent_name,
        "related_entities": related_entity_ids,
        "created_at": now,
    }


async def list_insights(limit: int = 50) -> list[dict]:
    """List recent knowledge insights."""
    if not settings.neo4j_enabled:
        return []

    from services.neo4j_connection import get_driver

    driver = await get_driver()
    results = []
    async with driver.session() as session:
        result = await session.run(
            """
            MATCH (k:Knowledge)
            OPTIONAL MATCH (k)-[:EXTRACTED_FROM]->(n)
            RETURN k.id AS id, k.content AS content, k.confidence AS confidence,
                   k.agent AS agent, k.created_at AS created_at,
                   collect(n.label) AS related_labels
            ORDER BY k.created_at DESC
            LIMIT $limit
            """,
            {"limit": limit},
        )
        async for rec in result:
            results.append({
                "id": rec["id"],
                "content": rec["content"],
                "confidence": rec["confidence"],
                "agent": rec["agent"],
                "created_at": rec["created_at"],
                "related_entities": rec["related_labels"],
            })
    return results
