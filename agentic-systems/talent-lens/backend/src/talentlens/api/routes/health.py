import logging

from fastapi import APIRouter
from sqlalchemy import text

from talentlens.dependencies import DBSession

logger = logging.getLogger(__name__)
router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check(db: DBSession):
    checks = {"status": "healthy", "database": "unknown"}
    try:
        await db.execute(text("SELECT 1"))
        checks["database"] = "connected"
    except Exception as e:
        logger.error("Database health check failed: %s", e)
        checks["database"] = "disconnected"
        checks["status"] = "degraded"
    return checks
