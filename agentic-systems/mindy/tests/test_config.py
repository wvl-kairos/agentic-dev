import os

import pytest
from unittest.mock import patch

from config import load_config, Config, VALID_REPORT_TYPES

VALID_ENV = {
    "ANTHROPIC_API_KEY": "ak-test",
    "LINEAR_API_KEY": "lk-test",
    "FIREFLIES_API_KEY": "fk-test",
    "GITHUB_TOKEN": "gh-test",
    "SLACK_BOT_TOKEN": "xoxb-test",
    "NOTION_TOKEN": "nt-test",
    "SLACK_CHANNEL_ID": "C-test",
}


def test_load_config_happy_path():
    with patch.dict(os.environ, VALID_ENV, clear=True):
        cfg = load_config()
    assert cfg.anthropic_api_key == "ak-test"
    assert cfg.dry_run is False
    assert cfg.report_type == "monday"


def test_load_config_dry_run_true():
    env = {**VALID_ENV, "DRY_RUN": "True"}
    with patch.dict(os.environ, env, clear=True):
        cfg = load_config()
    assert cfg.dry_run is True


def test_load_config_dry_run_uppercase():
    env = {**VALID_ENV, "DRY_RUN": "TRUE"}
    with patch.dict(os.environ, env, clear=True):
        cfg = load_config()
    assert cfg.dry_run is True


def test_load_config_raises_on_missing_required_key():
    env = {k: v for k, v in VALID_ENV.items() if k != "ANTHROPIC_API_KEY"}
    with patch.dict(os.environ, env, clear=True):
        with pytest.raises(EnvironmentError, match="ANTHROPIC_API_KEY"):
            load_config()


def test_load_config_report_type_friday():
    env = {**VALID_ENV, "REPORT_TYPE": "friday"}
    with patch.dict(os.environ, env, clear=True):
        cfg = load_config()
    assert cfg.report_type == "friday"


def test_load_config_invalid_report_type():
    env = {**VALID_ENV, "REPORT_TYPE": "wednesday"}
    with patch.dict(os.environ, env, clear=True):
        with pytest.raises(ValueError, match="Invalid REPORT_TYPE"):
            load_config()


def test_config_team_members_populated():
    with patch.dict(os.environ, VALID_ENV, clear=True):
        cfg = load_config()
    assert len(cfg.team_members) == 9
    assert "Rob Patrick" in cfg.team_members
    assert "Luis Suarez" in cfg.team_members


def test_config_accepts_custom_team_members():
    custom = ["Alice", "Bob"]
    cfg = Config(
        anthropic_api_key="x", linear_api_key="x", fireflies_api_key="x",
        github_token="x", slack_bot_token="x", notion_token="x",
        slack_channel_id="x", report_type="monday", dry_run=False,
        team_members=custom,
    )
    assert cfg.team_members == custom
