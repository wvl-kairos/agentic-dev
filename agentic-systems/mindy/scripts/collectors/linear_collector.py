"""Linear collector — fetches sprint data via GraphQL API."""

import logging
from datetime import datetime, timedelta, timezone

from retry import retry_request

logger = logging.getLogger("mindy.collectors.linear")

LINEAR_API = "https://api.linear.app/graphql"
REQUEST_TIMEOUT = 30


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


def _get_completed_issues(api_key: str, team_id: str, since: str) -> list:
    """Get issues completed since the given ISO date."""
    result = _query(api_key, """
        query($teamId: String!, $since: DateTime!) {
            team(id: $teamId) {
                issues(
                    filter: {
                        completedAt: { gte: $since }
                        state: { type: { eq: "completed" } }
                    }
                    first: 100
                    orderBy: updatedAt
                ) {
                    nodes {
                        id
                        identifier
                        title
                        completedAt
                        assignee { name }
                        project { name }
                    }
                }
            }
        }
    """, {"teamId": team_id, "since": since})

    issues = result.get("team", {}).get("issues", {}).get("nodes", [])
    logger.info("Completed issues since %s: %d", since, len(issues))
    return [
        {
            "id": i["id"],
            "identifier": i["identifier"],
            "title": i["title"],
            "completedAt": i["completedAt"],
            "assignee": (i.get("assignee") or {}).get("name", "Unassigned"),
            "project": (i.get("project") or {}).get("name", ""),
        }
        for i in issues
    ]


def _get_in_progress_issues(api_key: str, team_id: str) -> list:
    """Get issues currently in progress (started or unstarted with assignee)."""
    result = _query(api_key, """
        query($teamId: String!) {
            team(id: $teamId) {
                issues(
                    filter: {
                        state: { type: { in: ["started"] } }
                        assignee: { null: false }
                    }
                    first: 100
                ) {
                    nodes {
                        id
                        identifier
                        title
                        assignee { name }
                        state { name }
                        project { name }
                    }
                }
            }
        }
    """, {"teamId": team_id})

    issues = result.get("team", {}).get("issues", {}).get("nodes", [])
    logger.info("In-progress issues: %d", len(issues))
    return [
        {
            "id": i["id"],
            "identifier": i["identifier"],
            "title": i["title"],
            "assignee": (i.get("assignee") or {}).get("name", "Unassigned"),
            "state": (i.get("state") or {}).get("name", ""),
            "project": (i.get("project") or {}).get("name", ""),
        }
        for i in issues
    ]


def _get_ready_for_dev(api_key: str, team_id: str) -> list:
    """Get issues in 'Ready for Dev' state."""
    result = _query(api_key, """
        query($teamId: String!) {
            team(id: $teamId) {
                issues(
                    filter: {
                        state: { name: { eq: "Ready for Dev" } }
                    }
                    first: 100
                ) {
                    nodes {
                        id
                        identifier
                        title
                        assignee { name }
                        state { name }
                        project { name }
                    }
                }
            }
        }
    """, {"teamId": team_id})

    issues = result.get("team", {}).get("issues", {}).get("nodes", [])
    logger.info("Ready for dev issues: %d", len(issues))
    return [
        {
            "id": i["id"],
            "identifier": i["identifier"],
            "title": i["title"],
            "assignee": (i.get("assignee") or {}).get("name", "Unassigned"),
            "state": (i.get("state") or {}).get("name", ""),
            "project": (i.get("project") or {}).get("name", ""),
        }
        for i in issues
    ]


def collect(cfg) -> dict:
    """Collect all Linear data for the current sprint."""
    since = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()

    cycle = _get_active_cycle(cfg.linear_api_key, cfg.linear_team_id)
    completed = _get_completed_issues(cfg.linear_api_key, cfg.linear_team_id, since)
    in_progress = _get_in_progress_issues(cfg.linear_api_key, cfg.linear_team_id)
    ready_for_dev = _get_ready_for_dev(cfg.linear_api_key, cfg.linear_team_id)

    return {
        "current_cycle": cycle,
        "completed_this_week": completed,
        "in_progress": in_progress,
        "ready_for_dev": ready_for_dev,
    }
