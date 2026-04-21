import os
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Optional

logger = logging.getLogger("mindy.config")

VALID_REPORT_TYPES = {"monday", "friday"}


def _require_env(key: str) -> str:
    """Get a required environment variable or raise with a clear message."""
    val = os.environ.get(key)
    if not val:
        raise EnvironmentError(
            f"Required environment variable '{key}' is not set. "
            "Check your .env file or CI secrets configuration."
        )
    return val


@dataclass
class Config:
    anthropic_api_key: str
    linear_api_key: str
    fireflies_api_key: str
    github_token: str
    slack_bot_token: str
    notion_token: str
    slack_channel_id: str
    report_type: str  # "monday" | "friday"
    dry_run: bool

    # Kairos constants
    linear_team_id: str = "b4298b9c-8de9-427c-bee5-40c1ceba483f"
    linear_workspace: str = "wvl-kairos"
    github_org: str = "wvl-kairos"
    github_repo: str = "kairos"
    fireflies_organizer: str = "sunny.chalam@uplabs.us"
    notion_merges_db: str = "30a4f5abefac80f39bd7d2c67a970383"
    slack_read_channels: list = field(default_factory=lambda: [
        "C0A0JHS0LSE",   # #engineering
        "C0A0MUSMHFE",   # #all-kairos
        "C0A0N5E52JG",   # #data-team
    ])
    notion_merge_docs_url: str = (
        "https://www.notion.so/30a4f5abefac80f39bd7d2c67a970383"
        "?v=30a4f5abefac80e3ba44000c7655213d"
    )
    vault_path: str = "vault"
    claude_model: str = "claude-sonnet-4-20250514"

    # Time window for collectors. end_date=None means "now".
    # lookback_days controls how many days before end_date to pull data from.
    end_date: Optional[datetime] = None
    lookback_days: int = 7

    team_members: list = field(default_factory=list)

    def window_end(self) -> datetime:
        """End of the collection window — end_date if set, else now (UTC)."""
        return self.end_date or datetime.now(timezone.utc)

    def window_since(self) -> datetime:
        """Start of the collection window — window_end minus lookback_days."""
        return self.window_end() - timedelta(days=self.lookback_days)

    def __post_init__(self):
        if self.report_type not in VALID_REPORT_TYPES:
            raise ValueError(
                f"Invalid REPORT_TYPE '{self.report_type}'. "
                f"Must be one of: {sorted(VALID_REPORT_TYPES)}"
            )
        if not self.team_members:
            self.team_members = [
                "Rob Patrick",
                "Alex Maramaldo",
                "Antwoine Flowers",
                "Tomás Palomo",
                "Armando Lopez",
                "Evandro Machado",
                "Amanda Cunha",
                "Sunny Chalam",
                "Luis Suarez",
            ]


def load_config() -> Config:
    return Config(
        anthropic_api_key=_require_env("ANTHROPIC_API_KEY"),
        linear_api_key=_require_env("LINEAR_API_KEY"),
        fireflies_api_key=_require_env("FIREFLIES_API_KEY"),
        github_token=os.environ.get("GH_PAT") or _require_env("GITHUB_TOKEN"),
        slack_bot_token=_require_env("SLACK_BOT_TOKEN"),
        notion_token=_require_env("NOTION_TOKEN"),
        slack_channel_id=_require_env("SLACK_CHANNEL_ID"),
        report_type=os.environ.get("REPORT_TYPE", "monday"),
        dry_run=os.environ.get("DRY_RUN", "false").lower() == "true",
    )
