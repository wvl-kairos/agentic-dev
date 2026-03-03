"""Background assessment task.

Called via FastAPI BackgroundTasks when a webhook is received.
Runs the full assessment pipeline asynchronously.
"""

import logging
import uuid

from talentlens.database import async_session_factory
from talentlens.services.assessment.engine import run_assessment_pipeline

logger = logging.getLogger(__name__)


async def run_assessment(interview_id: uuid.UUID) -> None:
    """Background task entry point. Creates its own DB session."""
    logger.info("Starting assessment for interview %s", interview_id)
    try:
        async with async_session_factory() as db:
            assessment_id = await run_assessment_pipeline(interview_id, db)
            logger.info("Assessment %s completed for interview %s", assessment_id, interview_id)
    except Exception:
        logger.exception("Assessment failed for interview %s", interview_id)
