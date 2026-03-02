from __future__ import annotations

from typing import Any

from config import settings

GRAPH_TOOLS = [
    {
        "name": "query_graph",
        "description": "Search the knowledge graph for entities matching a term. Returns matching nodes with their properties and connections.",
        "input_schema": {
            "type": "object",
            "properties": {
                "search_term": {
                    "type": "string",
                    "description": "The term to search for in node labels and properties",
                }
            },
            "required": ["search_term"],
        },
    },
    {
        "name": "get_node",
        "description": "Get detailed information about a specific node by its ID.",
        "input_schema": {
            "type": "object",
            "properties": {
                "node_id": {
                    "type": "string",
                    "description": "The ID of the node to retrieve",
                }
            },
            "required": ["node_id"],
        },
    },
    {
        "name": "get_neighbors",
        "description": "Get all nodes connected to a specific node, including relationship types.",
        "input_schema": {
            "type": "object",
            "properties": {
                "node_id": {
                    "type": "string",
                    "description": "The ID of the node whose neighbors to retrieve",
                }
            },
            "required": ["node_id"],
        },
    },
    {
        "name": "graph_statistics",
        "description": "Get graph analytics: nodes ranked by number of connections (degree centrality), total node/edge counts, and relationship type distribution. Use this to answer questions about which nodes are most connected, graph structure, or general statistics.",
        "input_schema": {
            "type": "object",
            "properties": {
                "top_n": {
                    "type": "integer",
                    "description": "Number of top-connected nodes to return (default 10)",
                }
            },
            "required": [],
        },
    },
]


async def query_graph(search_term: str) -> list[dict[str, Any]]:
    if settings.neo4j_enabled:
        return await _query_neo4j(search_term)
    return _query_memory(search_term)


async def get_node(node_id: str) -> dict[str, Any]:
    if settings.neo4j_enabled:
        return await _get_node_neo4j(node_id)
    return _get_node_memory(node_id)


async def get_neighbors(node_id: str) -> list[dict[str, Any]]:
    if settings.neo4j_enabled:
        return await _get_neighbors_neo4j(node_id)
    return _get_neighbors_memory(node_id)


async def graph_statistics(top_n: int = 10) -> dict[str, Any]:
    if settings.neo4j_enabled:
        return await _graph_statistics_neo4j(top_n)
    return _graph_statistics_memory(top_n)


def _query_memory(search_term: str) -> list[dict[str, Any]]:
    from services.graph_manager import graph_manager

    graph = graph_manager.get_graph()
    results = []
    term_lower = search_term.lower()
    for node in graph.nodes:
        if term_lower in node.label.lower() or term_lower in node.id.lower():
            results.append({"id": node.id, "label": node.label, "type": node.type, "properties": node.properties})
    return results[:10]


def _get_node_memory(node_id: str) -> dict[str, Any]:
    from services.graph_manager import graph_manager

    graph = graph_manager.get_graph()
    for node in graph.nodes:
        if node.id == node_id:
            return {"id": node.id, "label": node.label, "type": node.type, "properties": node.properties}
    return {"error": "Node not found"}


def _get_neighbors_memory(node_id: str) -> list[dict[str, Any]]:
    from services.graph_manager import graph_manager

    graph = graph_manager.get_graph()
    results = []
    for edge in graph.edges:
        if edge.source == node_id or edge.target == node_id:
            other_id = edge.target if edge.source == node_id else edge.source
            other_node = next((n for n in graph.nodes if n.id == other_id), None)
            if other_node:
                results.append({
                    "id": other_node.id, "label": other_node.label,
                    "type": other_node.type, "relationship": edge.type,
                    "properties": other_node.properties,
                })
    return results


async def _query_neo4j(search_term: str) -> list[dict[str, Any]]:
    from services.neo4j_connection import get_driver

    driver = await get_driver()
    results = []
    async with driver.session() as session:
        result = await session.run(
            "MATCH (n) WHERE toLower(n.label) CONTAINS $term_lower OR toLower(n.id) CONTAINS $term_lower "
            "RETURN n.id AS id, n.label AS label, n.type AS type, properties(n) AS props LIMIT 10",
            {"term_lower": search_term.lower()},
        )
        async for rec in result:
            props = dict(rec["props"]) if rec["props"] else {}
            props.pop("id", None)
            props.pop("label", None)
            props.pop("type", None)
            results.append({"id": rec["id"], "label": rec["label"], "type": rec["type"], "properties": props})
    return results


async def _get_node_neo4j(node_id: str) -> dict[str, Any]:
    from services.neo4j_connection import get_driver

    driver = await get_driver()
    async with driver.session() as session:
        result = await session.run(
            "MATCH (n {id: $nid}) RETURN n.id AS id, n.label AS label, n.type AS type, properties(n) AS props",
            {"nid": node_id},
        )
        rec = await result.single()
        if not rec:
            return {"error": "Node not found"}
        props = dict(rec["props"]) if rec["props"] else {}
        props.pop("id", None)
        props.pop("label", None)
        props.pop("type", None)
        return {"id": rec["id"], "label": rec["label"], "type": rec["type"], "properties": props}


async def _get_neighbors_neo4j(node_id: str) -> list[dict[str, Any]]:
    from services.neo4j_connection import get_driver

    driver = await get_driver()
    results = []
    async with driver.session() as session:
        result = await session.run(
            "MATCH (n {id: $nid})-[r]-(m) "
            "RETURN m.id AS id, m.label AS label, m.type AS type, type(r) AS rel, properties(m) AS props LIMIT 20",
            {"nid": node_id},
        )
        async for rec in result:
            props = dict(rec["props"]) if rec["props"] else {}
            props.pop("id", None)
            props.pop("label", None)
            props.pop("type", None)
            results.append({
                "id": rec["id"], "label": rec["label"],
                "type": rec["type"], "relationship": rec["rel"],
                "properties": props,
            })
    return results


# ---------------------------------------------------------------------------
# Graph statistics (analytics)
# ---------------------------------------------------------------------------

def _graph_statistics_memory(top_n: int = 10) -> dict[str, Any]:
    from collections import Counter
    from services.graph_manager import graph_manager

    graph = graph_manager.get_graph()
    degree: Counter[str] = Counter()
    rel_types: Counter[str] = Counter()
    node_types: Counter[str] = Counter()

    for edge in graph.edges:
        degree[edge.source] += 1
        degree[edge.target] += 1
        rel_types[edge.type] += 1

    node_map = {n.id: n for n in graph.nodes}
    for n in graph.nodes:
        node_types[n.type] += 1

    top_nodes = []
    for nid, count in degree.most_common(top_n):
        node = node_map.get(nid)
        top_nodes.append({
            "id": nid,
            "label": node.label if node else nid,
            "type": node.type if node else "unknown",
            "connection_count": count,
        })

    return {
        "total_nodes": len(graph.nodes),
        "total_edges": len(graph.edges),
        "top_connected_nodes": top_nodes,
        "node_type_counts": dict(node_types),
        "relationship_type_counts": dict(rel_types),
    }


async def _graph_statistics_neo4j(top_n: int = 10) -> dict[str, Any]:
    from services.neo4j_connection import get_driver

    driver = await get_driver()
    async with driver.session() as session:
        # Top connected nodes
        result = await session.run(
            """
            MATCH (n)-[r]-()
            WITH n, COUNT(r) AS degree
            ORDER BY degree DESC
            LIMIT $top_n
            RETURN n.id AS id, n.label AS label, n.type AS type, degree
            """,
            {"top_n": top_n},
        )
        top_nodes = []
        async for rec in result:
            top_nodes.append({
                "id": rec["id"],
                "label": rec["label"],
                "type": rec["type"],
                "connection_count": rec["degree"],
            })

        # Total counts
        result = await session.run("MATCH (n) RETURN COUNT(n) AS cnt")
        total_nodes = (await result.single())["cnt"]

        result = await session.run("MATCH ()-[r]->() RETURN COUNT(r) AS cnt")
        total_edges = (await result.single())["cnt"]

        # Relationship type distribution
        result = await session.run(
            "MATCH ()-[r]->() RETURN type(r) AS rel_type, COUNT(r) AS cnt ORDER BY cnt DESC"
        )
        rel_types = {}
        async for rec in result:
            rel_types[rec["rel_type"]] = rec["cnt"]

        # Node type distribution
        result = await session.run(
            "MATCH (n) RETURN n.type AS node_type, COUNT(n) AS cnt ORDER BY cnt DESC"
        )
        node_types = {}
        async for rec in result:
            node_types[rec["node_type"] or "unknown"] = rec["cnt"]

    return {
        "total_nodes": total_nodes,
        "total_edges": total_edges,
        "top_connected_nodes": top_nodes,
        "node_type_counts": node_types,
        "relationship_type_counts": rel_types,
    }
