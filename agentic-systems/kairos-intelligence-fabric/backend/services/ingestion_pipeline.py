from __future__ import annotations

import asyncio
import logging
import re
from datetime import datetime, timezone

from config import settings
from models.ingestion_models import ExtractedEntity, IngestionResult
from services.document_manager import document_manager

logger = logging.getLogger(__name__)

# Track ingestion status per document
_ingestion_results: dict[str, IngestionResult] = {}


def get_ingestion_status(doc_id: str) -> IngestionResult | None:
    return _ingestion_results.get(doc_id)


async def run_ingestion(doc_id: str) -> IngestionResult:
    """Full ingestion pipeline: chunk + embed, extract entities, create edges."""
    result = IngestionResult(document_id=doc_id, status="processing")
    _ingestion_results[doc_id] = result

    try:
        # Update document status
        document_manager.update_status(doc_id, "ingesting")

        # Get document content
        content = document_manager.get_document_content(doc_id)
        if not content:
            result.status = "error"
            result.error_message = "Document content not found"
            document_manager.update_status(doc_id, "error")
            return result

        # Step 1: Chunk, embed, and index in ChromaDB + BM25
        if settings.openai_api_key:
            from services.chunking_service import chunk_document
            from services.vector_store import add_chunks, delete_document_chunks
            from services.hybrid_retriever import rebuild_bm25_index

            doc = document_manager.get_document(doc_id)
            doc_title = doc.title if doc else doc_id

            # Clear old chunks if re-ingesting
            await asyncio.to_thread(delete_document_chunks, doc_id)

            # Chunk and embed
            doc_filename = doc.filename if doc else ""
            chunks = chunk_document(
                doc_id, doc_title, content,
                max_chunk_size=settings.rag_max_chunk_size,
                filename=doc_filename,
            )
            added = await asyncio.to_thread(add_chunks, chunks)
            logger.info("Indexed %d chunks for document %s", added, doc_id)

            # Rebuild BM25 index
            await asyncio.to_thread(rebuild_bm25_index)
        else:
            logger.warning("OpenAI API key not set — skipping chunking/embedding")

        # Step 2: Extract entity references from the document text
        extracted = _extract_entity_references(content)
        result.entities_extracted = len(extracted)
        result.extracted_entities = extracted

        # Step 3: Resolve entities against ontology and create edges
        if extracted:
            if settings.neo4j_enabled:
                resolved_count, edges_count, new_nodes_count = await _resolve_and_link(doc_id, extracted)
            else:
                resolved_count, edges_count, new_nodes_count = _resolve_in_memory(doc_id, extracted)
            result.entities_resolved = resolved_count
            result.edges_created = edges_count
            result.nodes_created = new_nodes_count

        result.status = "completed"
        document_manager.update_status(doc_id, "ingested")

        # Persist graph state and get final totals
        from services.graph_manager import graph_manager
        try:
            graph_manager.save_to_disk()
            g = graph_manager.get_graph()
            result.graph_total_nodes = len(g.nodes)
            result.graph_total_edges = len(g.edges)
        except Exception:
            pass

        logger.info(
            "Ingestion complete for %s: %d entities, %d resolved, %d new nodes, %d edges, graph total: %d nodes %d edges",
            doc_id, result.entities_extracted, result.entities_resolved,
            result.nodes_created, result.edges_created,
            result.graph_total_nodes, result.graph_total_edges,
        )

    except Exception as e:
        logger.error("Ingestion failed for %s: %s", doc_id, e)
        result.status = "error"
        result.error_message = str(e)
        document_manager.update_status(doc_id, "error")

    _ingestion_results[doc_id] = result
    return result


def _extract_entity_references(content: str) -> list[ExtractedEntity]:
    """Extract entity IDs and known names from document text.

    Looks for patterns like (equip-cnc-a7), (prod-gear-set), (supp-precision-steel),
    (person-lzhang), (line-assembly-1), etc.
    """
    entities: list[ExtractedEntity] = []
    seen: set[str] = set()

    # Pattern: parenthesized IDs like (equip-cnc-a7)
    id_pattern = re.compile(r"\(([a-z]+-[a-z0-9-]+)\)")
    for match in id_pattern.finditer(content):
        entity_id = match.group(1)
        if entity_id not in seen:
            seen.add(entity_id)
            # Determine type from prefix
            prefix = entity_id.split("-")[0]
            type_map = {
                "equip": "equipment",
                "prod": "products",
                "ord": "orders",
                "supp": "suppliers",
                "person": "people",
                "line": "production_lines",
                "qual": "quality",
            }
            entities.append(ExtractedEntity(
                name=entity_id,
                entity_type=type_map.get(prefix, ""),
                matched_node_id=entity_id,
                similarity_score=1.0,
            ))

    return entities


_PREFIX_TO_TYPE = {
    "equip": "equipment",
    "prod": "products",
    "ord": "orders",
    "supp": "suppliers",
    "person": "people",
    "line": "production_lines",
    "qual": "quality",
    "mat": "materials",
    "maint": "maintenance",
    "safety": "safety",
    "logis": "logistics",
    "org": "organizational",
}

_NEO4J_LABEL_MAP = {
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
}


def _resolve_in_memory(doc_id: str, entities: list[ExtractedEntity]) -> tuple[int, int, int]:
    """Resolve entity references against the in-memory graph (no Neo4j).

    - Entities that match existing node IDs are counted as resolved.
    - Entities without a match get a new node created in the graph.
    - A DOCUMENTED_IN edge is created from each entity to a Document node.

    Returns (resolved_count, edges_created, new_nodes_created).
    """
    from models.graph_models import NodeModel, EdgeModel
    from services.graph_manager import graph_manager

    graph = graph_manager.get_graph()
    existing_ids = {n.id for n in graph.nodes}
    now = datetime.now(timezone.utc).isoformat()

    resolved = 0
    new_nodes = 0
    edges = 0

    # Create document node if it doesn't exist
    if doc_id not in existing_ids:
        doc = document_manager.get_document(doc_id)
        graph.nodes.append(NodeModel(
            id=doc_id,
            type="document",
            label=doc.title if doc else doc_id,
            properties={"source": "document_ingestion", "ingested_at": now},
        ))
        existing_ids.add(doc_id)
        new_nodes += 1

    for entity in entities:
        entity_id = entity.matched_node_id
        if not entity_id:
            continue

        if entity_id in existing_ids:
            resolved += 1
        else:
            # Create new node
            prefix = entity_id.split("-")[0]
            entity_type = _PREFIX_TO_TYPE.get(prefix, "")
            label = entity_id.replace("-", " ").title()
            graph.nodes.append(NodeModel(
                id=entity_id,
                type=entity_type or "unknown",
                label=label,
                properties={
                    "source": "document_ingestion",
                    "discovered_in": doc_id,
                },
            ))
            existing_ids.add(entity_id)
            resolved += 1
            new_nodes += 1
            logger.info("Created in-memory node %s (type: %s)", entity_id, entity_type)

        # Create DOCUMENTED_IN edge
        graph.edges.append(EdgeModel(
            source=entity_id,
            target=doc_id,
            type="DOCUMENTED_IN",
            properties={"extracted_at": now},
        ))
        edges += 1

    # Update metadata
    graph.metadata.total_nodes = len(graph.nodes)
    graph.metadata.total_edges = len(graph.edges)
    graph.metadata.last_updated = now

    logger.info(
        "In-memory resolve for %s: %d resolved, %d new nodes, %d edges",
        doc_id, resolved, new_nodes, edges,
    )
    return resolved, edges, new_nodes


async def _resolve_and_link(doc_id: str, entities: list[ExtractedEntity]) -> tuple[int, int, int]:
    """Resolve entity references and link them to the ontology graph.

    Returns (resolved_count, edges_created, new_nodes_created).
    """
    from services.neo4j_connection import get_driver

    driver = await get_driver()
    resolved = 0
    edges = 0
    new_nodes = 0
    now = datetime.now(timezone.utc).isoformat()

    async with driver.session() as session:
        # Ensure document node exists — check if it's new
        result = await session.run(
            "MATCH (d:Document {id: $doc_id}) RETURN d.id AS id",
            {"doc_id": doc_id},
        )
        doc_existed = await result.single()
        await session.run(
            "MERGE (d:Document {id: $doc_id}) SET d.type = 'document', d.label = $doc_id",
            {"doc_id": doc_id},
        )
        if not doc_existed:
            new_nodes += 1

        for entity in entities:
            entity_id = entity.matched_node_id
            if not entity_id:
                continue

            # Step 1: Check if node already exists (exact match)
            result = await session.run(
                "MATCH (n {id: $nid}) RETURN n.id AS id",
                {"nid": entity_id},
            )
            record = await result.single()

            if record:
                # Exact match — node already in graph
                resolved += 1
            else:
                # Step 2: No exact match — create instance node and link to type node
                prefix = entity_id.split("-")[0]
                entity_type = _PREFIX_TO_TYPE.get(prefix, "")
                neo4j_label = _NEO4J_LABEL_MAP.get(entity_type, "Entity")
                label = entity_id.replace("-", " ").title()

                await session.run(
                    f"""
                    MERGE (n:{neo4j_label} {{id: $id}})
                    SET n.type = $type,
                        n.label = $label,
                        n.source = 'document_ingestion',
                        n.discovered_in = $doc_id
                    """,
                    {
                        "id": entity_id,
                        "type": entity_type,
                        "label": label,
                        "doc_id": doc_id,
                    },
                )

                result = await session.run(
                    "MATCH (t) WHERE t.id STARTS WITH $prefix AND t.source = 'ontology_engine' RETURN t.id AS id LIMIT 1",
                    {"prefix": f"{prefix}-"},
                )
                type_record = await result.single()
                if type_record:
                    await session.run(
                        """
                        MATCH (inst {id: $inst_id}), (t {id: $type_id})
                        MERGE (inst)-[r:INSTANCE_OF]->(t)
                        SET r.created_at = $now
                        """,
                        {
                            "inst_id": entity_id,
                            "type_id": type_record["id"],
                            "now": now,
                        },
                    )

                resolved += 1
                new_nodes += 1
                logger.info(
                    "Created instance node %s (type: %s, linked to: %s)",
                    entity_id, entity_type,
                    type_record["id"] if type_record else "none",
                )

            # Step 3: Create DOCUMENTED_IN edge
            await session.run(
                """
                MATCH (d:Document {id: $doc_id}), (n {id: $node_id})
                MERGE (n)-[r:DOCUMENTED_IN]->(d)
                SET r.extracted_at = $now
                """,
                {
                    "doc_id": doc_id,
                    "node_id": entity_id,
                    "now": now,
                },
            )
            edges += 1

    # Update in-memory graph to reflect new nodes/edges
    await _sync_graph_from_neo4j()

    return resolved, edges, new_nodes


async def _sync_graph_from_neo4j() -> None:
    """Refresh the in-memory graph from Neo4j after ingestion adds nodes."""
    try:
        if settings.neo4j_enabled:
            from services.neo4j_manager import Neo4jGraphManager
            from services.graph_manager import graph_manager

            manager = Neo4jGraphManager()
            graph = await manager.get_graph()
            graph_manager.update_graph(graph)
    except Exception as e:
        logger.warning("Failed to sync graph from Neo4j: %s", e)
