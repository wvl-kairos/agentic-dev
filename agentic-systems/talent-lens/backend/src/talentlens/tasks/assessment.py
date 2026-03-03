"""Background assessment tasks.

Called via FastAPI BackgroundTasks when a webhook is received.
"""

import logging
import uuid

from talentlens.database import async_session_factory
from talentlens.services.assessment.engine import run_assessment_pipeline

logger = logging.getLogger(__name__)


async def process_interview(interview_id: uuid.UUID) -> None:
    """Background task: run the full assessment pipeline for an interview.

    Creates its own DB session since BackgroundTasks run outside the request lifecycle.
    """
    logger.info("Starting assessment pipeline for interview %s", interview_id)
    try:
        async with async_session_factory() as db:
            assessment_id = await run_assessment_pipeline(interview_id, db)
            logger.info(
                "Assessment %s created for interview %s",
                assessment_id,
                interview_id,
            )
    except Exception:
        logger.exception("Assessment pipeline failed for interview %s", interview_id)
