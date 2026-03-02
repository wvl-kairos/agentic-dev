import logging
import re

from fastapi import APIRouter, HTTPException

from config import settings
from models.graph_models import GraphResponse

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/graph", response_model=GraphResponse)
async def get_graph():
    try:
        if settings.neo4j_enabled:
            from services.neo4j_manager import Neo4jGraphManager

            manager = Neo4jGraphManager()
            return await manager.get_graph()
        else:
            from services.graph_manager import graph_manager

            return graph_manager.get_graph()
    except RuntimeError:
        raise HTTPException(status_code=503, detail="Graph data unavailable")


@router.post("/graph/reset", response_model=GraphResponse)
async def reset_graph():
    """Wipe Neo4j, re-write baseline ontology, restore in-memory graph."""
    from services.graph_manager import graph_manager

    restored = graph_manager.restore_baseline()
    if restored is None:
        raise HTTPException(status_code=404, detail="No baseline snapshot available")

    # Reset document statuses back to "uploaded" so they can be re-ingested
    from services.document_manager import document_manager
    for doc in document_manager.list_documents():
        if doc.status in ("ingested", "ingesting", "error"):
            document_manager.update_status(doc.id, "uploaded")

    # Also reset Neo4j if enabled
    if settings.neo4j_enabled:
        try:
            await _reset_neo4j(restored)
        except Exception as e:
            logger.warning("Neo4j reset failed (in-memory still restored): %s", e)

    return restored


_LABEL_MAP = {
    "equipment": "Equipment",
    "products": "Product",
    "orders": "Order",
    "suppliers": "Supplier",
    "quality": "Quality",
    "people": "Person",
    "production_lines": "ProductionLine",
    "materials": "Material",
    "maintenance": "Maintenance",
    "logistics": "Logistics",
    "safety": "Safety",
    "organizational": "Organization",
    "document": "Document",
    "knowledge": "Knowledge",
}


async def _reset_neo4j(graph: GraphResponse) -> None:
    """Delete all nodes/edges from Neo4j, then re-write the baseline graph."""
    from services.neo4j_connection import get_driver

    driver = await get_driver()
    async with driver.session() as session:
        # Wipe everything
        await session.run("MATCH (n) DETACH DELETE n")
        logger.info("Neo4j wiped")

        # Re-create baseline nodes
        for node in graph.nodes:
            neo4j_label = _LABEL_MAP.get(node.type, "Entity")
            await session.run(
                f"CREATE (n:{neo4j_label} {{id: $id}}) SET n.type = $type, n.label = $label, n.source = 'ontology_engine'",
                {"id": node.id, "type": node.type, "label": node.label},
            )

        # Re-create baseline edges
        for edge in graph.edges:
            rel_type = re.sub(r"[^A-Z_]", "_", edge.type.upper())
            await session.run(
                f"MATCH (a {{id: $source}}), (b {{id: $target}}) CREATE (a)-[:{rel_type}]->(b)",
                {"source": edge.source, "target": edge.target},
            )

    logger.info("Neo4j reset: %d nodes, %d edges written", len(graph.nodes), len(graph.edges))
