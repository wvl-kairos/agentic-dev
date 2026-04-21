"""GitHub collector — fetches merged PRs and commit activity."""

import logging
from datetime import datetime, timedelta, timezone

from retry import retry_request

logger = logging.getLogger("mindy.collectors.github")

GITHUB_API = "https://api.github.com"
REQUEST_TIMEOUT = 30


def _get_headers(token: str) -> dict:
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }


def _get_merged_prs(token: str, repo: str, since: datetime, until: datetime) -> list:
    """Get PRs merged to main within the given date window."""
    since_str = since.strftime("%Y-%m-%d")
    until_str = until.strftime("%Y-%m-%d")
    query = f"repo:{repo} is:pr is:merged base:main merged:{since_str}..{until_str}"

    resp = retry_request("GET",
        f"{GITHUB_API}/search/issues",
        headers=_get_headers(token),
        params={"q": query, "sort": "updated", "order": "desc", "per_page": 50},
        timeout=REQUEST_TIMEOUT,
    )
    resp.raise_for_status()
    items = resp.json().get("items", [])

    prs = []
    for item in items:
        prs.append({
            "number": item["number"],
            "title": item["title"],
            "author": (item.get("user") or {}).get("login", "unknown"),
            "merged_at": item.get("pull_request", {}).get("merged_at", ""),
            "body": (item.get("body") or "")[:200],
        })

    logger.info("Merged PRs since %s: %d", since_str, len(prs))
    return prs


def _get_commit_authors(token: str, repo: str, since: datetime, until: datetime) -> dict:
    """Get commit author counts for the given window."""
    resp = retry_request("GET",
        f"{GITHUB_API}/repos/{repo}/commits",
        headers=_get_headers(token),
        params={"since": since.isoformat(), "until": until.isoformat(), "per_page": 100},
        timeout=REQUEST_TIMEOUT,
    )
    resp.raise_for_status()
    commits = resp.json()

    authors = {}
    for commit in commits:
        author = (commit.get("author") or {}).get("login")
        if not author:
            author = (commit.get("commit", {}).get("author") or {}).get("name", "unknown")
        authors[author] = authors.get(author, 0) + 1

    logger.info("Commit authors this week: %s", authors)
    return authors


def collect(cfg) -> dict:
    """Collect GitHub data: merged PRs and commit authors."""
    since = cfg.window_since()
    until = cfg.window_end()
    repo = f"{cfg.github_org}/{cfg.github_repo}"

    merged_prs = _get_merged_prs(cfg.github_token, repo, since, until)
    authors_by_count = _get_commit_authors(cfg.github_token, repo, since, until)

    return {
        "merged_prs": merged_prs,
        "authors_by_count": authors_by_count,
    }
