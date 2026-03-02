from __future__ import annotations

from typing import Any

from config import settings

ANALYTICS_TOOLS = [
    {
        "name": "get_equipment_metrics",
        "description": "Get OEE, utilization, MTBF, and other metrics for equipment. Can retrieve for a specific equipment ID or all equipment.",
        "input_schema": {
            "type": "object",
            "properties": {
                "equipment_id": {
                    "type": "string",
                    "description": "Optional specific equipment ID. If omitted, returns all equipment metrics.",
                }
            },
        },
    },
    {
        "name": "compare_equipment",
        "description": "Compare metrics between two or more equipment items.",
        "input_schema": {
            "type": "object",
            "properties": {
                "equipment_ids": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of equipment IDs to compare",
                }
            },
            "required": ["equipment_ids"],
        },
    },
]


async def get_equipment_metrics(equipment_id: str = "") -> dict[str, Any] | list[dict[str, Any]]:
    """Get metrics from graph nodes with equipment type."""
    if settings.neo4j_enabled:
        return await _get_metrics_neo4j(equipment_id)
    return _get_metrics_memory(equipment_id)


def _get_metrics_memory(equipment_id: str = "") -> dict[str, Any] | list[dict[str, Any]]:
    from services.graph_manager import graph_manager

    graph = graph_manager.get_graph()
    results = []
    for node in graph.nodes:
        if node.type != "equipment":
            continue
        if equipment_id and node.id != equipment_id:
            continue
        metrics = {
            "id": node.id,
            "label": node.label,
            "oee": node.properties.get("oee"),
            "utilization": node.properties.get("utilization"),
            "mtbf_hours": node.properties.get("mtbf_hours"),
            "status": node.properties.get("status"),
            "department": node.properties.get("department"),
            "last_maintenance": node.properties.get("last_maintenance"),
        }
        if equipment_id:
            return metrics
        results.append(metrics)
    if equipment_id:
        return {"error": "Equipment not found"}
    return results


async def _get_metrics_neo4j(equipment_id: str = "") -> dict[str, Any] | list[dict[str, Any]]:
    from services.neo4j_connection import get_driver

    driver = await get_driver()
    results = []
    async with driver.session() as session:
        if equipment_id:
            result = await session.run(
                "MATCH (n:Equipment {id: $eid}) RETURN properties(n) AS props",
                {"eid": equipment_id},
            )
            rec = await result.single()
            if not rec:
                return {"error": "Equipment not found"}
            return dict(rec["props"])
        else:
            result = await session.run("MATCH (n:Equipment) RETURN properties(n) AS props")
            async for rec in result:
                results.append(dict(rec["props"]))
    return results


async def compare_equipment(equipment_ids: list[str]) -> list[dict[str, Any]]:
    results = []
    for eid in equipment_ids:
        metrics = await get_equipment_metrics(eid)
        if isinstance(metrics, dict):
            results.append(metrics)
    return results
