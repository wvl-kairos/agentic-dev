"""Fireflies collector — fetches standup transcripts via GraphQL API."""

import logging
from datetime import datetime, timedelta, timezone

from retry import retry_request

logger = logging.getLogger("mindy.collectors.fireflies")

FIREFLIES_API = "https://api.fireflies.ai/graphql"
REQUEST_TIMEOUT = 30


def _query(api_key: str, query: str, variables: dict = None) -> dict:
    """Execute a Fireflies GraphQL query with retry."""
    resp = retry_request(
        "POST", FIREFLIES_API,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json={"query": query, "variables": variables or {}},
        timeout=REQUEST_TIMEOUT,
    )
    resp.raise_for_status()
    data = resp.json()
    if "errors" in data:
        raise RuntimeError(f"Fireflies GraphQL errors: {data['errors']}")
    return data.get("data", {})


def _get_transcripts(api_key: str, organizer_email: str, since: datetime) -> list:
    """Get standup transcripts from the past week."""
    result = _query(api_key, """
        query($fromDate: DateTime, $toDate: DateTime) {
            transcripts(fromDate: $fromDate, toDate: $toDate) {
                id
                title
                date
                organizer_email
                participants
                summary {
                    action_items
                    overview
                    shorthand_bullet
                }
            }
        }
    """, {
        "fromDate": since.isoformat(),
        "toDate": datetime.now(timezone.utc).isoformat(),
    })

    transcripts = result.get("transcripts") or []

    # Filter by organizer
    filtered = [
        t for t in transcripts
        if (t.get("organizer_email") or "").lower() == organizer_email.lower()
    ]

    logger.info(
        "Fireflies transcripts: %d total, %d from %s",
        len(transcripts), len(filtered), organizer_email,
    )

    return [
        {
            "id": t["id"],
            "title": t.get("title", ""),
            "date": t.get("date", ""),
            "participants": t.get("participants") or [],
            "action_items": (t.get("summary") or {}).get("action_items") or [],
            "overview": (t.get("summary") or {}).get("overview", ""),
            "bullets": (t.get("summary") or {}).get("shorthand_bullet") or [],
        }
        for t in filtered
    ]


def collect(cfg) -> dict:
    """Collect standup data from Fireflies."""
    since = datetime.now(timezone.utc) - timedelta(days=7)
    standups = _get_transcripts(cfg.fireflies_api_key, cfg.fireflies_organizer, since)

    return {"standups": standups}
