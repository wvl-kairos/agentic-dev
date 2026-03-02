"""Seed the Neo4j database with sample_ontology.json data.

Usage:
    cd backend && python -m scripts.seed_ontology

Uses MERGE so it's idempotent — safe to run multiple times.
"""

from __future__ import annotations

import asyncio
import json
import logging
import sys
from pathlib import Path

from neo4j import AsyncGraphDatabase

# Allow running from backend/ directory
sys.path.insert(0, str(Path(__file__).parent.parent))
from config import settings  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

TYPE_TO_LABEL = {
    "equipment": "Equipment",
    "products": "Product",
    "orders": "Order",
    "quality": "Quality",
    "people": "Person",
    "suppliers": "Supplier",
    "production_lines": "ProductionLine",
}


async def seed() -> None:
    data_path = Path(__file__).parent.parent / "data" / "sample_ontology.json"
    raw = json.loads(data_path.read_text())
    nodes = raw["nodes"]
    edges = raw["edges"]

    if not settings.neo4j_uri:
        logger.error("NEO4J_URI not set. Cannot seed.")
        sys.exit(1)

    driver = AsyncGraphDatabase.driver(
        settings.neo4j_uri,
        auth=(settings.neo4j_username, settings.neo4j_password),
    )

    async with driver.session() as session:
        # Create constraints for each label
        for label in TYPE_TO_LABEL.values():
            await session.run(
                f"CREATE CONSTRAINT IF NOT EXISTS FOR (n:{label}) REQUIRE n.id IS UNIQUE"
            )
        logger.info("Constraints created/verified")

        # Seed nodes
        for node in nodes:
            label = TYPE_TO_LABEL.get(node["type"], "Entity")
            props = {
                "id": node["id"],
                "type": node["type"],
                "label": node["label"],
                **node.get("properties", {}),
            }
            # Build props string for Cypher
            prop_keys = ", ".join(f"{k}: ${k}" for k in props)
            query = f"MERGE (n:{label} {{id: $id}}) SET n = {{{prop_keys}}}"
            await session.run(query, props)

        logger.info("Seeded %d nodes", len(nodes))

        # Seed edges
        for edge in edges:
            rel_type = edge["type"]
            props = edge.get("properties", {})
            prop_set = ""
            if props:
                assignments = ", ".join(f"r.{k} = ${k}" for k in props)
                prop_set = f" SET {assignments}"

            query = (
                f"MATCH (a {{id: $source}}), (b {{id: $target}}) "
                f"MERGE (a)-[r:{rel_type}]->(b){prop_set}"
            )
            params = {"source": edge["source"], "target": edge["target"], **props}
            await session.run(query, params)

        logger.info("Seeded %d edges", len(edges))

    await driver.close()
    logger.info("Seed complete")


if __name__ == "__main__":
    asyncio.run(seed())
