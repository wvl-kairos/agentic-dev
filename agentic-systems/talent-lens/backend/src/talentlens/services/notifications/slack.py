"""Slack notification service.

Sends assessment summaries and candidate updates to configured Slack channels.
"""

import logging

from talentlens.config import settings

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
    if not settings.slack_bot_token:
        logger.info(
            "Slack not configured — would notify: %s %s assessment: %.1f/5 (%s)",
            candidate_name,
            stage,
            overall_score,
            recommendation,
        )
        return

    from slack_sdk.web.async_client import AsyncWebClient

    client = AsyncWebClient(token=settings.slack_bot_token)
    target_channel = channel or settings.slack_default_channel

    if not target_channel:
        logger.warning("No Slack channel configured, skipping notification")
        return

    # Score emoji
    if overall_score >= 4.0:
        emoji = ":large_green_circle:"
    elif overall_score >= 3.0:
        emoji = ":large_yellow_circle:"
    else:
        emoji = ":red_circle:"

    text = (
        f"{emoji} *{candidate_name}* — {stage} assessment complete\n"
        f"Score: *{overall_score:.1f}/5.0* | Recommendation: *{recommendation}*\n"
        f"<{scorecard_url}|View Scorecard>"
    )

    await client.chat_postMessage(channel=target_channel, text=text, mrkdwn=True)
    logger.info("Slack notification sent to %s for %s", target_channel, candidate_name)
