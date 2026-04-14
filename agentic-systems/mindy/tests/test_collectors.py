"""Tests for all 5 collectors with mocked HTTP responses."""

from unittest.mock import MagicMock, patch
from datetime import datetime, timezone

import pytest

from collectors import (
    linear_collector,
    github_collector,
    fireflies_collector,
    notion_collector,
    slack_collector,
)


def _make_cfg():
    cfg = MagicMock()
    cfg.linear_api_key = "lin-test"
    cfg.linear_team_id = "team-123"
    cfg.github_token = "gh-test"
    cfg.github_org = "wvl-kairos"
    cfg.github_repo = "kairos"
    cfg.fireflies_api_key = "ff-test"
    cfg.fireflies_organizer = "sunny@test.com"
    cfg.notion_token = "nt-test"
    cfg.notion_merges_db = "db-123"
    cfg.slack_bot_token = "xoxb-test"
    cfg.slack_channel_id = "C-test"
    return cfg


def _mock_resp(json_data):
    """Create a mock response that behaves like requests.Response."""
    resp = MagicMock()
    resp.status_code = 200
    resp.json.return_value = json_data
    resp.raise_for_status = MagicMock()
    return resp


# === Linear collector ===

class TestLinearCollector:
    PATCH_TARGET = "collectors.linear_collector.retry_request"

    def _gql_resp(self, data):
        return _mock_resp({"data": data})

    def test_collect_returns_all_keys(self):
        cycle_resp = self._gql_resp({
            "team": {"activeCycle": {"id": "c1", "name": "Sprint 10", "number": 10, "startsAt": "2026-04-07", "endsAt": "2026-04-14"}}
        })
        issues_resp = self._gql_resp({
            "team": {"issues": {"nodes": [
                {"id": "i1", "identifier": "PDEV-100", "title": "Test issue", "completedAt": "2026-04-10", "assignee": {"name": "Rob Patrick"}, "project": {"name": "C1"}}
            ]}}
        })
        in_progress_resp = self._gql_resp({"team": {"issues": {"nodes": []}}})
        ready_resp = self._gql_resp({"team": {"issues": {"nodes": []}}})

        with patch(self.PATCH_TARGET, side_effect=[cycle_resp, issues_resp, in_progress_resp, ready_resp]):
            result = linear_collector.collect(_make_cfg())

        assert "current_cycle" in result
        assert result["current_cycle"]["name"] == "Sprint 10"
        assert len(result["completed_this_week"]) == 1
        assert result["completed_this_week"][0]["assignee"] == "Rob Patrick"
        assert "in_progress" in result
        assert "ready_for_dev" in result

    def test_handles_null_assignee(self):
        cycle_resp = self._gql_resp({"team": {"activeCycle": None}})
        issues_resp = self._gql_resp({
            "team": {"issues": {"nodes": [
                {"id": "i2", "identifier": "PDEV-200", "title": "No assignee", "completedAt": "2026-04-10", "assignee": None, "project": None}
            ]}}
        })
        empty_resp = self._gql_resp({"team": {"issues": {"nodes": []}}})

        with patch(self.PATCH_TARGET, side_effect=[cycle_resp, issues_resp, empty_resp, empty_resp]):
            result = linear_collector.collect(_make_cfg())

        assert result["completed_this_week"][0]["assignee"] == "Unassigned"
        assert result["completed_this_week"][0]["project"] == ""

    def test_graphql_error_raises(self):
        resp = _mock_resp({"errors": [{"message": "bad query"}]})

        with patch(self.PATCH_TARGET, return_value=resp):
            with pytest.raises(RuntimeError, match="GraphQL errors"):
                linear_collector.collect(_make_cfg())


# === GitHub collector ===

class TestGitHubCollector:
    PATCH_TARGET = "collectors.github_collector.retry_request"

    def test_collect_returns_prs_and_authors(self):
        pr_resp = _mock_resp({"items": [
            {"number": 42, "title": "Fix bug", "user": {"login": "rob"}, "pull_request": {"merged_at": "2026-04-10T12:00:00Z"}, "body": "Fixed it"}
        ]})
        commits_resp = _mock_resp([
            {"author": {"login": "rob"}, "commit": {"author": {"name": "Rob"}}},
            {"author": {"login": "rob"}, "commit": {"author": {"name": "Rob"}}},
            {"author": {"login": "alex"}, "commit": {"author": {"name": "Alex"}}},
        ])

        with patch(self.PATCH_TARGET, side_effect=[pr_resp, commits_resp]):
            result = github_collector.collect(_make_cfg())

        assert len(result["merged_prs"]) == 1
        assert result["merged_prs"][0]["author"] == "rob"
        assert result["authors_by_count"]["rob"] == 2
        assert result["authors_by_count"]["alex"] == 1

    def test_truncates_pr_body(self):
        pr_resp = _mock_resp({"items": [
            {"number": 1, "title": "Big PR", "user": {"login": "dev"}, "pull_request": {"merged_at": ""}, "body": "x" * 500}
        ]})
        commits_resp = _mock_resp([])

        with patch(self.PATCH_TARGET, side_effect=[pr_resp, commits_resp]):
            result = github_collector.collect(_make_cfg())

        assert len(result["merged_prs"][0]["body"]) == 200


# === Fireflies collector ===

class TestFirefliesCollector:
    PATCH_TARGET = "collectors.fireflies_collector.retry_request"

    def test_collect_filters_by_organizer(self):
        resp = _mock_resp({"data": {"transcripts": [
            {"id": "t1", "title": "Standup", "date": "2026-04-10", "organizer_email": "sunny@test.com", "participants": ["Rob", "Alex"], "summary": {"action_items": ["Fix bug"], "overview": "Discussed sprint", "shorthand_bullet": ["Fix bug"]}},
            {"id": "t2", "title": "Other meeting", "date": "2026-04-10", "organizer_email": "other@test.com", "participants": [], "summary": None},
        ]}})

        with patch(self.PATCH_TARGET, return_value=resp):
            result = fireflies_collector.collect(_make_cfg())

        assert len(result["standups"]) == 1
        assert result["standups"][0]["title"] == "Standup"
        assert result["standups"][0]["action_items"] == ["Fix bug"]

    def test_handles_null_summary(self):
        resp = _mock_resp({"data": {"transcripts": [
            {"id": "t3", "title": "Standup", "date": "2026-04-10", "organizer_email": "sunny@test.com", "participants": [], "summary": None},
        ]}})

        with patch(self.PATCH_TARGET, return_value=resp):
            result = fireflies_collector.collect(_make_cfg())

        assert result["standups"][0]["action_items"] == []
        assert result["standups"][0]["overview"] == ""


# === Notion collector ===

class TestNotionCollector:
    PATCH_TARGET = "collectors.notion_collector.retry_request"

    def test_collect_extracts_title_and_url(self):
        resp = _mock_resp({"results": [
            {
                "id": "page-1",
                "url": "https://notion.so/page-1",
                "created_time": "2026-04-10T12:00:00Z",
                "properties": {
                    "Name": {
                        "type": "title",
                        "title": [{"plain_text": "Sprint 10 Merge Doc"}],
                    }
                },
            }
        ]})

        with patch(self.PATCH_TARGET, return_value=resp):
            result = notion_collector.collect(_make_cfg())

        assert len(result["merge_docs"]) == 1
        assert result["merge_docs"][0]["title"] == "Sprint 10 Merge Doc"
        assert result["merge_docs"][0]["url"] == "https://notion.so/page-1"

    def test_empty_database(self):
        resp = _mock_resp({"results": []})

        with patch(self.PATCH_TARGET, return_value=resp):
            result = notion_collector.collect(_make_cfg())

        assert result["merge_docs"] == []


# === Slack collector ===

class TestSlackCollector:
    PATCH_TARGET = "collectors.slack_collector.retry_request"

    def test_collect_filters_user_messages(self):
        resp = _mock_resp({
            "ok": True,
            "messages": [
                {"type": "message", "ts": "1234.5678", "user": "U1", "text": "hello"},
                {"type": "message", "subtype": "channel_join", "ts": "1234.5679", "user": "U2", "text": "joined"},
                {"type": "message", "ts": "1234.5680", "user": "U3", "text": "world"},
            ],
        })

        with patch(self.PATCH_TARGET, return_value=resp):
            result = slack_collector.collect(_make_cfg())

        assert len(result["messages"]) == 2
        assert result["messages"][0]["text"] == "hello"
        assert result["messages"][1]["text"] == "world"

    def test_raises_on_slack_error(self):
        resp = _mock_resp({"ok": False, "error": "channel_not_found"})

        with patch(self.PATCH_TARGET, return_value=resp):
            with pytest.raises(RuntimeError, match="channel_not_found"):
                slack_collector.collect(_make_cfg())
