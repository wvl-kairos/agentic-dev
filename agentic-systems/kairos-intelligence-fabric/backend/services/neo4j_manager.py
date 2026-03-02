from __future__ import annotations

import logging
from typing import Any

from models.graph_models import EdgeModel, GraphMetadata, GraphResponse, NodeModel
from services.neo4j_connection import get_driver

logger = logging.getLogger(__name__)


class Neo4jGraphManager:
    """Neo4j-backed graph store implementing the GraphStore protocol."""

    async def get_graph(self) -> GraphResponse:
        driver = await get_driver()
        nodes: list[NodeModel] = []
        edges: list[EdgeModel] = []
        seen_nodes: set[str] = set()

        async with driver.session() as session:
            # Fetch all nodes
            result = await session.run(
                "MATCH (n) WHERE n.id IS NOT NULL RETURN n, labels(n) AS labels"
            )
            async for record in result:
                node = record["n"]
                node_id = node.get("id")
                if node_id and node_id not in seen_nodes:
                    seen_nodes.add(node_id)
                    props = dict(node)
                    node_type = props.pop("type", _label_to_type(record["labels"]))
                    label = props.pop("label", node_id)
                    props.pop("id", None)
                    nodes.append(
                        NodeModel(
                            id=node_id,
                            type=node_type,
                            label=label,
                            properties=props,
                        )
                    )

            # Fetch all relationships
            result = await session.run(
                """
                MATCH (a)-[r]->(b)
                WHERE a.id IS NOT NULL AND b.id IS NOT NULL
                RETURN a.id AS source, b.id AS target, type(r) AS rel_type,
                       properties(r) AS props
                """
            )
            async for record in result:
                props: dict[str, Any] = dict(record["props"]) if record["props"] else {}
                edges.append(
                    EdgeModel(
                        source=record["source"],
                        target=record["target"],
                        type=record["rel_type"],
                        properties=props,
                    )
                )

        return GraphResponse(
            nodes=nodes,
            edges=edges,
            metadata=GraphMetadata(
                total_nodes=len(nodes),
                total_edges=len(edges),
                ontology_version="2.0",
                last_updated="2026-02-19T00:00:00Z",
            ),
        )


def _label_to_type(labels: list[str]) -> str:
    """Convert Neo4j labels to our type system."""
    type_map = {
        "Equipment": "equipment",
        "Product": "products",
        "Order": "orders",
        "Quality": "quality",
        "Person": "people",
        "Supplier": "suppliers",
        "ProductionLine": "production_lines",
        "Document": "document",
        "Knowledge": "knowledge",
    }
    for label in labels:
        if label in type_map:
            return type_map[label]
    return labels[0].lower() if labels else "unknown"
