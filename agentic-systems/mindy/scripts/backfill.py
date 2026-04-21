"""One-shot backfill: iterates weekly Mondays for the last N weeks and runs
the orchestrator with DRY_RUN=true for each, enriching the vault with
historical sprint files, standup notes, and per-person/project history.

Usage:
    python3.11 scripts/backfill.py [--weeks 12]

No Slack posts. No automatic git commits. Meant to be run locally once.
"""

import argparse
import dataclasses
import logging
import time
from datetime import datetime, timedelta, timezone

from config import load_config
from orchestrator import orchestrate

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("mindy.backfill")

SLEEP_BETWEEN_WEEKS_SEC = 10


def _monday_of(dt: datetime) -> datetime:
    """Return the Monday 14:00 UTC (matching the real cron) of the week containing dt."""
    monday = dt - timedelta(days=dt.weekday())
    return monday.replace(hour=14, minute=0, second=0, microsecond=0)


def _week_ends(now: datetime, weeks: int) -> list:
    """Return the Monday reference dates for the last `weeks` weeks, oldest first."""
    this_monday = _monday_of(now)
    return [this_monday - timedelta(weeks=i) for i in reversed(range(weeks))]


def run(weeks: int = 12):
    base_cfg = load_config()
    now = datetime.now(timezone.utc)
    dates = _week_ends(now, weeks)

    logger.info("=== Mindy Backfill ===")
    logger.info("Weeks: %d | DRY_RUN forced to true | No Slack posts", weeks)
    logger.info("Window range: %s → %s", dates[0].date(), dates[-1].date())

    for idx, week_end in enumerate(dates, start=1):
        logger.info("")
        logger.info("─── Week %d/%d — ending %s ───", idx, weeks, week_end.date())
        cfg = dataclasses.replace(
            base_cfg,
            dry_run=True,
            report_type="monday",
            end_date=week_end,
            lookback_days=7,
        )
        try:
            orchestrate(cfg)
        except Exception as exc:
            logger.error("Week %d failed: %s — continuing", idx, exc)

        if idx < len(dates):
            logger.info("Sleeping %ds before next week...", SLEEP_BETWEEN_WEEKS_SEC)
            time.sleep(SLEEP_BETWEEN_WEEKS_SEC)

    logger.info("")
    logger.info("=== Backfill complete: %d weeks processed ===", weeks)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run a historical Mindy backfill.")
    parser.add_argument("--weeks", type=int, default=12, help="Number of weeks to backfill (default: 12)")
    args = parser.parse_args()
    run(weeks=args.weeks)
