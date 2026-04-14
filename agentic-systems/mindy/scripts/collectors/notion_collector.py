"""Notion collector — fetches recent merge docs from a database."""

import logging
from datetime import datetime, timedelta, timezone

from retry import retry_request

logger = logging.getLogger("mindy.collectors.notion")

NOTION_API = "https://api.notion.com/v1"
NOTION_VERSION = "2022-06-28"
REQUEST_TIMEOUT = 30


def _get_headers(token: str) -> dict:
    return {
        "Authorization": f"Bearer {token}",
        "Notion-Version": NOTION_VERSION,
        "Content-Type": "application/json",
    }


def _get_recent_pages(token: str, database_id: str, since: datetime) -> list:
    """Query a Notion database for pages created in the last N days."""
    since_str = since.isoformat()

    resp = retry_request(
        "POST", f"{NOTION_API}/databases/{database_id}/query",
        headers=_get_headers(token),
        json={
            "filter": {
                "timestamp": "created_time",
                "created_time": {"on_or_after": since_str},
            },
            "sorts": [
                {"timestamp": "created_time", "direction": "descending"}
            ],
            "page_size": 50,
        },
        timeout=REQUEST_TIMEOUT,
    )
    resp.raise_for_status()
    results = resp.json().get("results", [])

    pages = []
    for page in results:
        # Extract title from properties
        title = ""
        for prop in page.get("properties", {}).values():
            if prop.get("type") == "title":
                title_parts = prop.get("title", [])
                title = "".join(t.get("plain_text", "") for t in title_parts)
                break

        pages.append({
            "id": page["id"],
            "title": title,
            "url": page.get("url", ""),
            "created_time": page.get("created_time", ""),
        })

    logger.info("Notion merge docs since %s: %d", since_str[:10], len(pages))
    return pages


def collect(cfg) -> dict:
    """Collect recent merge docs from Notion."""
    since = datetime.now(timezone.utc) - timedelta(days=7)
    merge_docs = _get_recent_pages(cfg.notion_token, cfg.notion_merges_db, since)

    return {"merge_docs": merge_docs}
