from fastapi import APIRouter

from config import settings

router = APIRouter()


@router.get("/health")
async def health_check():
    response = {
        "status": "healthy",
        "version": "2.0.0",
        "service": "cerebro-fabric-backend",
        "graph_store": "neo4j" if settings.neo4j_enabled else "in-memory",
    }

    if settings.neo4j_enabled:
        from services.neo4j_connection import check_neo4j_health

        neo4j_ok = await check_neo4j_health()
        response["neo4j"] = "connected" if neo4j_ok else "disconnected"
        if not neo4j_ok:
            response["status"] = "degraded"

    return response
