"""Background assessment tasks.

Called via FastAPI BackgroundTasks when a webhook is received.
Runs talk ratio + contribution detection, updates the Interview record.
"""

import logging
import uuid

from talentlens.database import async_session_factory
from talentlens.models.database.interview import Interview
from talentlens.services.assessment.contribution import detect_contributions
from talentlens.services.assessment.talk_ratio import compute_talk_ratio

logger = logging.getLogger(__name__)


async def process_interview(interview_id: uuid.UUID) -> None:
    """Background task: run talk ratio + contribution detection on an interview."""
    logger.info("Processing interview %s", interview_id)

    async with async_session_factory() as db:
        interview = await db.get(Interview, interview_id)
        if not interview:
            logger.error("Interview %s not found", interview_id)
            return

        if not interview.diarization:
            logger.warning("Interview %s has no diarization data, skipping analysis", interview_id)
            return

        # 1. Compute talk ratio
        talk_result = compute_talk_ratio(interview.diarization)
        interview.talk_ratio = talk_result["candidate_ratio"]
        logger.info(
            "Interview %s talk ratio: %.0f%% (%s)",
            interview_id,
            talk_result["candidate_ratio"] * 100,
            talk_result["candidate_speaker"],
        )

        # 2. Detect contributions
        contributions = {}
        if interview.transcript:
            contributions = detect_contributions(
                interview.transcript,
                candidate_speaker=talk_result["candidate_speaker"],
            )
            logger.info(
                "Interview %s contributions: %d individual, %d collective (ratio: %.0f%%)",
                interview_id,
                contributions.get("individual_count", 0),
                contributions.get("collective_count", 0),
                contributions.get("ratio", 0) * 100,
            )

        # Store analysis results in diarization metadata
        interview.diarization = {
            "segments": interview.diarization,
            "analysis": {
                "talk_ratio": talk_result,
                "contributions": contributions,
            },
        }

        await db.commit()
        logger.info("Interview %s processing complete", interview_id)
