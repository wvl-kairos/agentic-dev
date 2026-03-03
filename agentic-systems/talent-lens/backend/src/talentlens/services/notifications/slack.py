"""Slack notification service.

Sends assessment summaries and candidate updates to configured Slack channels.
"""

import logging

logger = logging.getLogger(__name__)


async def notify_assessment_complete(
    candidate_name: str,
    stage: str,
    overall_score: float,
    recommendation: str,
    scorecard_url: str,
    channel: str | None = None,
) -> None:
    """Send Slack notification when an assessment is completed."""
    # TODO: format Block Kit message with score, recommendation, link
    # TODO: send via slack_sdk WebClient
    raise NotImplementedError
