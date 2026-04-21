"""Tests for claude_client with mocked Anthropic API."""

import json
from unittest.mock import MagicMock, patch

import pytest

import claude_client


def _make_cfg():
    cfg = MagicMock()
    cfg.anthropic_api_key = "test-key"
    cfg.claude_model = "claude-sonnet-4-20250514"
    cfg.notion_merge_docs_url = "https://notion.so/test"
    return cfg


def _mock_anthropic_response(text: str):
    """Create a mock Anthropic message response."""
    message = MagicMock()
    content_block = MagicMock()
    content_block.text = text
    message.content = [content_block]
    return message


class TestCompileVaultUpdates:
    def test_parses_valid_json_response(self):
        vault_updates = {
            "sprint_file": "# Sprint 16",
            "people_updates": {"rob-patrick": "# Rob"},
            "projects_updates": {"Order Visibility": "# Order Visibility"},
            "index_update": "# Index",
            "standup_notes": "# Standups",
            "new_decisions": [],
        }
        response = _mock_anthropic_response(json.dumps(vault_updates))

        with patch("claude_client.anthropic.Anthropic") as MockClient:
            MockClient.return_value.messages.create.return_value = response
            result = claude_client.compile_vault_updates({}, "", _make_cfg())

        assert result["sprint_file"] == "# Sprint 16"
        assert "rob-patrick" in result["people_updates"]

    def test_strips_code_fences(self):
        vault_updates = {
            "sprint_file": "# Sprint",
            "people_updates": {},
            "projects_updates": {},
            "index_update": "",
            "standup_notes": "",
            "new_decisions": [],
        }
        fenced = f"```json\n{json.dumps(vault_updates)}\n```"
        response = _mock_anthropic_response(fenced)

        with patch("claude_client.anthropic.Anthropic") as MockClient:
            MockClient.return_value.messages.create.return_value = response
            result = claude_client.compile_vault_updates({}, "", _make_cfg())

        assert result["sprint_file"] == "# Sprint"

    def test_raises_on_invalid_json(self):
        response = _mock_anthropic_response("This is not JSON at all")

        with patch("claude_client.anthropic.Anthropic") as MockClient:
            MockClient.return_value.messages.create.return_value = response
            with pytest.raises(RuntimeError, match="invalid JSON"):
                claude_client.compile_vault_updates({}, "", _make_cfg())

    def test_passes_correct_model(self):
        vault_updates = {
            "sprint_file": "", "people_updates": {}, "projects_updates": {},
            "index_update": "", "standup_notes": "", "new_decisions": [],
        }
        response = _mock_anthropic_response(json.dumps(vault_updates))

        with patch("claude_client.anthropic.Anthropic") as MockClient:
            MockClient.return_value.messages.create.return_value = response
            cfg = _make_cfg()
            cfg.claude_model = "claude-sonnet-4-20250514"
            claude_client.compile_vault_updates({"linear": {}}, "context", cfg)

        call_kwargs = MockClient.return_value.messages.create.call_args[1]
        assert call_kwargs["model"] == "claude-sonnet-4-20250514"
        assert call_kwargs["max_tokens"] == 16384
        assert "knowledge base compiler" in call_kwargs["system"]


class TestGenerateMindyReport:
    def test_returns_report_text(self):
        report = "*Kairos Weekly Kickoff*\nContent here"
        response = _mock_anthropic_response(report)

        with patch("claude_client.anthropic.Anthropic") as MockClient:
            MockClient.return_value.messages.create.return_value = response
            result = claude_client.generate_mindy_report({}, "", "monday", _make_cfg())

        assert result == report

    def test_monday_report_type(self):
        response = _mock_anthropic_response("monday report")

        with patch("claude_client.anthropic.Anthropic") as MockClient:
            MockClient.return_value.messages.create.return_value = response
            claude_client.generate_mindy_report({}, "", "monday", _make_cfg())

        call_kwargs = MockClient.return_value.messages.create.call_args[1]
        assert "MONDAY KICKOFF" in call_kwargs["messages"][0]["content"]

    def test_friday_report_type(self):
        response = _mock_anthropic_response("friday report")

        with patch("claude_client.anthropic.Anthropic") as MockClient:
            MockClient.return_value.messages.create.return_value = response
            claude_client.generate_mindy_report({}, "", "friday", _make_cfg())

        call_kwargs = MockClient.return_value.messages.create.call_args[1]
        assert "FRIDAY WRAP-UP" in call_kwargs["messages"][0]["content"]

    def test_includes_notion_url(self):
        response = _mock_anthropic_response("report")

        with patch("claude_client.anthropic.Anthropic") as MockClient:
            MockClient.return_value.messages.create.return_value = response
            cfg = _make_cfg()
            cfg.notion_merge_docs_url = "https://notion.so/merge-docs"
            claude_client.generate_mindy_report({}, "", "monday", cfg)

        call_kwargs = MockClient.return_value.messages.create.call_args[1]
        assert "https://notion.so/merge-docs" in call_kwargs["messages"][0]["content"]

    def test_uses_mindy_system_prompt(self):
        response = _mock_anthropic_response("report")

        with patch("claude_client.anthropic.Anthropic") as MockClient:
            MockClient.return_value.messages.create.return_value = response
            claude_client.generate_mindy_report({}, "", "monday", _make_cfg())

        call_kwargs = MockClient.return_value.messages.create.call_args[1]
        assert "Mindy" in call_kwargs["system"]
        assert "radio DJ" in call_kwargs["system"]
        assert "*text*" in call_kwargs["system"]  # Slack formatting rule
