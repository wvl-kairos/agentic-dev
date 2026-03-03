"""Assessment engine — core orchestrator for the evaluation pipeline.

Pipeline per interview:
1. Compute talk ratio from diarization
2. Detect individual contributions ("I built" vs "we built")
3. Score against rubric criteria via Claude API
4. Persist Assessment + CriterionScores + Evidence
5. Advance candidate pipeline stage
6. Send Slack notification
"""

import logging
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


async def run_assessment_pipeline(interview_id: uuid.UUID, db: AsyncSession) -> uuid.UUID:
    """Run the full assessment pipeline for an interview.
    Returns the created Assessment ID."""
    # TODO: load interview + candidate + rubric
    # TODO: compute talk ratio
    # TODO: detect contributions
    # TODO: call Claude for scoring
    # TODO: persist results
    # TODO: advance candidate stage
    # TODO: notify via Slack
    raise NotImplementedError
