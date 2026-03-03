"""Dashboard metrics endpoints."""

from fastapi import APIRouter

from talentlens.dependencies import DBSession

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/metrics")
async def get_dashboard_metrics(db: DBSession):
    """Aggregate metrics: candidates per stage, avg scores, pipeline velocity."""
    # TODO: implement aggregate queries
    return {
        "candidates_by_stage": {},
        "avg_scores_by_venture": {},
        "pipeline_velocity_days": None,
    }
