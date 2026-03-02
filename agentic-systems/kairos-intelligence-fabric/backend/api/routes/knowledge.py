from fastapi import APIRouter

from services.crystallization_service import list_insights

router = APIRouter()


@router.get("/knowledge")
async def get_knowledge(limit: int = 50):
    insights = await list_insights(limit=limit)
    return {"insights": insights, "total": len(insights)}


@router.get("/knowledge/{insight_id}")
async def get_insight(insight_id: str):
    from config import settings

    if not settings.neo4j_enabled:
        return {"error": "Neo4j not configured"}

    from services.neo4j_connection import get_driver

    driver = await get_driver()
    async with driver.session() as session:
        result = await session.run(
            """
            MATCH (k:Knowledge {id: $kid})
            OPTIONAL MATCH (k)-[:EXTRACTED_FROM]->(n)
            RETURN k.id AS id, k.content AS content, k.confidence AS confidence,
                   k.agent AS agent, k.query AS query, k.created_at AS created_at,
                   collect({id: n.id, label: n.label, type: n.type}) AS related
            """,
            {"kid": insight_id},
        )
        rec = await result.single()
        if not rec:
            return {"error": "Insight not found"}
        return {
            "id": rec["id"],
            "content": rec["content"],
            "confidence": rec["confidence"],
            "agent": rec["agent"],
            "query": rec["query"],
            "created_at": rec["created_at"],
            "related_entities": rec["related"],
        }
