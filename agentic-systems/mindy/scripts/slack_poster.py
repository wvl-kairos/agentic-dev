import logging
import time

import requests

logger = logging.getLogger("mindy.slack")

SLACK_MAX_CHARS = 1900
MAX_CHUNKS = 20
MAX_RETRIES = 3


def _post_with_retry(payload: dict, session: requests.Session) -> dict:
    """Post to Slack with retry on rate-limit (429) and transient errors."""
    for attempt in range(MAX_RETRIES):
        resp = session.post(
            "https://slack.com/api/chat.postMessage",
            json=payload,
            timeout=30,
        )
        if resp.status_code == 429:
            retry_after = int(resp.headers.get("Retry-After", 5))
            logger.warning("Slack rate-limited, retrying in %ds (attempt %d)", retry_after, attempt + 1)
            time.sleep(retry_after)
            continue
        resp.raise_for_status()
        data = resp.json()
        if not data.get("ok"):
            raise RuntimeError(f"Slack API error: {data.get('error', 'unknown')}")
        return data
    raise RuntimeError(f"Slack API: failed after {MAX_RETRIES} retries")


def post_message(channel_id: str, text: str, session: requests.Session) -> str:
    """Post a message to a Slack channel. Returns the message timestamp."""
    data = _post_with_retry({"channel": channel_id, "text": text}, session)
    return data["ts"]


def post_thread_reply(channel_id: str, thread_ts: str, text: str, session: requests.Session) -> str:
    """Post a threaded reply. Returns the reply timestamp."""
    data = _post_with_retry(
        {"channel": channel_id, "text": text, "thread_ts": thread_ts}, session
    )
    return data["ts"]


def _make_session(token: str) -> requests.Session:
    """Create a requests session with Slack auth header for connection reuse."""
    s = requests.Session()
    s.headers.update({"Authorization": f"Bearer {token}"})
    return s


def split_and_post(channel_id: str, text: str, token: str) -> str:
    """Post a message, splitting into thread replies if over SLACK_MAX_CHARS.

    Splits on newline boundaries. Returns the main message timestamp.
    """
    session = _make_session(token)
    try:
        if len(text) <= SLACK_MAX_CHARS:
            return post_message(channel_id, text, session)

        # Split into chunks on newline boundaries
        chunks = []
        pos = 0
        while pos < len(text):
            end = pos + SLACK_MAX_CHARS
            if end >= len(text):
                chunks.append(text[pos:])
                break
            split_at = text.rfind("\n", pos, end)
            if split_at == -1 or split_at == pos:
                split_at = end
            chunks.append(text[pos:split_at])
            pos = split_at
            # Skip leading newlines
            while pos < len(text) and text[pos] == "\n":
                pos += 1

            if len(chunks) >= MAX_CHUNKS:
                logger.warning("Report exceeded %d chunks, truncating", MAX_CHUNKS)
                if pos < len(text):
                    chunks.append(text[pos:pos + SLACK_MAX_CHARS])
                break

        ts = post_message(channel_id, chunks[0], session)
        for chunk in chunks[1:]:
            post_thread_reply(channel_id, ts, chunk, session)

        return ts
    finally:
        session.close()
