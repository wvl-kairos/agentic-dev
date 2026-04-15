"""Slack collector — fetches recent channel messages for context."""

import logging
from datetime import datetime, timedelta, timezone

from retry import retry_request

logger = logging.getLogger("mindy.collectors.slack")

SLACK_API = "https://slack.com/api"
REQUEST_TIMEOUT = 30


def _get_channel_history(token: str, channel_id: str, since: datetime) -> list:
    """Get recent messages from a Slack channel."""
    oldest = str(since.timestamp())

    resp = retry_request(
        "GET", f"{SLACK_API}/conversations.history",
        headers={"Authorization": f"Bearer {token}"},
        params={
            "channel": channel_id,
            "oldest": oldest,
            "limit": 200,
        },
        timeout=REQUEST_TIMEOUT,
    )
    resp.raise_for_status()
    data = resp.json()

    if not data.get("ok"):
        raise RuntimeError(f"Slack API error: {data.get('error', 'unknown')}")

    messages = data.get("messages", [])
    logger.info("Slack messages from #%s: %d", channel_id, len(messages))

    return [
        {
            "ts": msg.get("ts", ""),
            "user": msg.get("user", ""),
            "text": msg.get("text", ""),
            "channel": channel_id,
        }
        for msg in messages
        if msg.get("type") == "message" and not msg.get("subtype")
    ]


def collect(cfg) -> dict:
    """Collect recent messages from multiple read channels."""
    since = datetime.now(timezone.utc) - timedelta(days=7)
    all_messages = []

    for channel_id in cfg.slack_read_channels:
        try:
            msgs = _get_channel_history(cfg.slack_bot_token, channel_id, since)
            all_messages.extend(msgs)
        except Exception as exc:
            logger.warning("Failed to read channel %s: %s", channel_id, exc)

    logger.info("Total Slack messages collected: %d", len(all_messages))
    return {"messages": all_messages}
