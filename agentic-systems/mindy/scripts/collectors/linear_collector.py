"""Linear collector — fetches sprint data via GraphQL API."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from retry import retry_request

logger = logging.getLogger("mindy.collectors.linear")

LINEAR_API = "https://api.linear.app/graphql"
REQUEST_TIMEOUT = 30

# Shared fragment for issue fields we care about
ISSUE_FIELDS = """
    id
    identifier
    title
    completedAt
    updatedAt
    assignee { name }
    state { name type }
    project { name }
"""


def _query(api_key: str, query: str, variables: dict = None) -> dict:
    """Execute a Linear GraphQL query with retry."""
    resp = retry_request(
        "POST", LINEAR_API,
        headers={
            "Authorization": api_key,
            "Content-Type": "application/json",
        },
        json={"query": query, "variables": variables or {}},
        timeout=REQUEST_TIMEOUT,
    )
    resp.raise_for_status()
    data = resp.json()
    if "errors" in data:
        raise RuntimeError(f"Linear GraphQL errors: {data['errors']}")
    return data["data"]


def _get_active_cycle(api_key: str, team_id: str) -> dict | None:
    """Get the current active cycle for the team."""
    result = _query(api_key, """
        query($teamId: String!) {
            team(id: $teamId) {
                activeCycle {
                    id
                    name
                    number
                    startsAt
                    endsAt
                }
            }
        }
    """, {"teamId": team_id})

    cycle = result.get("team", {}).get("activeCycle")
    if cycle:
        logger.info("Active cycle: %s (#%s)", cycle.get("name"), cycle.get("number"))
    else:
        logger.warning("No active cycle found")
    return cycle


def _get_issues_by_state_type(api_key: str, team_id: str, state_type: str) -> list:
    """Get issues filtered by state type (completed, started, unstarted, etc.)."""
    result = _query(api_key, f"""
        query($teamId: String!) {{
            team(id: $teamId) {{
                issues(
                    filter: {{ state: {{ type: {{ eq: "{state_type}" }} }} }}
                    first: 100
                    orderBy: updatedAt
                ) {{
                    nodes {{ {ISSUE_FIELDS} }}
                }}
            }}
        }}
    """, {"teamId": team_id})

    return result.get("team", {}).get("issues", {}).get("nodes", [])


def _format_issue(issue: dict) -> dict:
    """Normalize a raw Linear issue into our standard format."""
    return {
        "id": issue["id"],
        "identifier": issue["identifier"],
        "title": issue["title"],
        "completedAt": issue.get("completedAt", ""),
        "assignee": (issue.get("assignee") or {}).get("name", "Unassigned"),
        "state": (issue.get("state") or {}).get("name", ""),
        "project": (issue.get("project") or {}).get("name", ""),
    }


def collect(cfg) -> dict:
    """Collect all Linear data for the current sprint."""
    since = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()

    cycle = _get_active_cycle(cfg.linear_api_key, cfg.linear_team_id)

    # Get completed issues, filter by date in Python (avoids GraphQL filter issues)
    raw_completed = _get_issues_by_state_type(cfg.linear_api_key, cfg.linear_team_id, "completed")
    completed = [
        _format_issue(i) for i in raw_completed
        if (i.get("completedAt") or "") >= since
    ]
    logger.info("Completed issues since %s: %d (of %d total)", since[:10], len(completed), len(raw_completed))

    # Get in-progress issues
    raw_started = _get_issues_by_state_type(cfg.linear_api_key, cfg.linear_team_id, "started")
    in_progress = [_format_issue(i) for i in raw_started]
    logger.info("In-progress issues: %d", len(in_progress))

    # Get unstarted issues, filter for "Ready for Dev" in Python
    raw_unstarted = _get_issues_by_state_type(cfg.linear_api_key, cfg.linear_team_id, "unstarted")
    ready_for_dev = [
        _format_issue(i) for i in raw_unstarted
        if (i.get("state") or {}).get("name") == "Ready for Dev"
    ]
    logger.info("Ready for dev issues: %d", len(ready_for_dev))

    return {
        "current_cycle": cycle,
        "completed_this_week": completed,
        "in_progress": in_progress,
        "ready_for_dev": ready_for_dev,
    }
