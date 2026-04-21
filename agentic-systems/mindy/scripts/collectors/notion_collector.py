"""Notion collector — fetches recent workspace activity and merge docs."""

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


def _extract_title(page: dict) -> str:
    """Extract the title from a Notion page's properties."""
    for prop in page.get("properties", {}).values():
        if prop.get("type") == "title":
            title_parts = prop.get("title", [])
            return "".join(t.get("plain_text", "") for t in title_parts)
    return ""


def _search_recent_pages(token: str, since: datetime, until: datetime) -> list:
    """Search entire workspace for pages created or edited within the window."""
    since_str = since.isoformat()
    until_str = until.isoformat()

    resp = retry_request(
        "POST", f"{NOTION_API}/search",
        headers=_get_headers(token),
        json={
            "filter": {"property": "object", "value": "page"},
            "sort": {"direction": "descending", "timestamp": "last_edited_time"},
            "page_size": 50,
        },
        timeout=REQUEST_TIMEOUT,
    )
    resp.raise_for_status()
    results = resp.json().get("results", [])

    pages = []
    for page in results:
        edited = page.get("last_edited_time", "")
        created = page.get("created_time", "")
        # Only include pages active within the window (edited or created between since..until)
        edited_in_window = since_str <= edited <= until_str
        created_in_window = since_str <= created <= until_str
        if not (edited_in_window or created_in_window):
            continue

        title = _extract_title(page)
        if not title:
            continue

        pages.append({
            "id": page["id"],
            "title": title,
            "url": page.get("url", ""),
            "created_time": created,
            "last_edited_time": edited,
            "is_new": created_in_window,
        })

    logger.info("Notion workspace pages (updated %s..%s): %d", since_str[:10], until_str[:10], len(pages))
    return pages


def _get_merge_docs(token: str, database_id: str, since: datetime, until: datetime) -> list:
    """Query the Merges database for merge docs created within the window."""
    since_str = since.isoformat()
    until_str = until.isoformat()

    resp = retry_request(
        "POST", f"{NOTION_API}/databases/{database_id}/query",
        headers=_get_headers(token),
        json={
            "filter": {
                "and": [
                    {"timestamp": "created_time", "created_time": {"on_or_after": since_str}},
                    {"timestamp": "created_time", "created_time": {"on_or_before": until_str}},
                ],
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
        title = _extract_title(page)
        pages.append({
            "id": page["id"],
            "title": title,
            "url": page.get("url", ""),
            "created_time": page.get("created_time", ""),
        })

    logger.info("Notion merge docs %s..%s: %d", since_str[:10], until_str[:10], len(pages))
    return pages


def collect(cfg) -> dict:
    """Collect recent Notion activity: workspace pages + merge docs."""
    since = cfg.window_since()
    until = cfg.window_end()

    # 1. Search entire workspace for recent activity
    recent_pages = _search_recent_pages(cfg.notion_token, since, until)

    # 2. Query merge docs database (may fail if not shared with integration)
    merge_docs = []
    try:
        merge_docs = _get_merge_docs(cfg.notion_token, cfg.notion_merges_db, since, until)
    except Exception as exc:
        logger.warning("Merge docs query failed (non-fatal): %s", exc)

    return {
        "recent_pages": recent_pages,
        "merge_docs": merge_docs,
    }
