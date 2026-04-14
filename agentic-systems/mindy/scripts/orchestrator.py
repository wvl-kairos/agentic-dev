"""Mindy orchestrator — main entrypoint.

Collects data from all sources, updates the vault, generates a report,
and posts it to Slack.
"""

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

from config import load_config
from collectors import (
    linear_collector,
    fireflies_collector,
    github_collector,
    notion_collector,
    slack_collector,
)
from vault import vault_reader, vault_writer
import claude_client
import slack_poster

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("mindy.orchestrator")

COLLECTOR_TIMEOUT = 60  # seconds per collector


def run_collectors(cfg):
    """Run all collectors in parallel, return merged dict."""
    collectors = {
        "linear": lambda: linear_collector.collect(cfg),
        "fireflies": lambda: fireflies_collector.collect(cfg),
        "github": lambda: github_collector.collect(cfg),
        "notion": lambda: notion_collector.collect(cfg),
        "slack": lambda: slack_collector.collect(cfg),
    }

    results = {}
    with ThreadPoolExecutor(max_workers=5) as pool:
        futures = {pool.submit(fn): name for name, fn in collectors.items()}
        for future in as_completed(futures, timeout=COLLECTOR_TIMEOUT * len(collectors)):
            name = futures[future]
            try:
                results[name] = future.result(timeout=COLLECTOR_TIMEOUT)
                logger.info("[%s] collected OK", name)
            except TimeoutError:
                logger.error("[%s] TIMED OUT after %ds", name, COLLECTOR_TIMEOUT)
                results[name] = {"error": "timeout"}
            except Exception as exc:
                logger.error("[%s] FAILED: %s", name, exc)
                results[name] = {"error": str(exc)}

    # Surface collection failures
    failed = [name for name, val in results.items() if "error" in val]
    if failed:
        logger.warning("%d collector(s) failed: %s", len(failed), failed)
        results["_collection_warnings"] = {"failed_sources": failed}

    return results


def main():
    logger.info("=== Mindy Orchestrator ===")

    # 1. Load config
    cfg = load_config()
    logger.info("Report type: %s | Dry run: %s", cfg.report_type, cfg.dry_run)

    # 2. Run all collectors
    logger.info("Step 1/5: Collecting data...")
    raw_data = run_collectors(cfg)

    # 3. Read existing vault for context
    logger.info("Step 2/5: Reading vault context...")
    vault_context = vault_reader.build_context_bundle(cfg)

    # 4. Compile vault updates via Claude
    logger.info("Step 3/5: Compiling vault updates via Claude...")
    try:
        vault_updates = claude_client.compile_vault_updates(raw_data, vault_context, cfg)
    except NotImplementedError:
        logger.info("[SKIP] compile_vault_updates not yet implemented")
        vault_updates = {}

    try:
        written = vault_writer.write_all(vault_updates, cfg)
        logger.info("Wrote %d vault files", len(written))
    except Exception as exc:
        logger.warning("Vault write failed: %s", exc)

    # 5. Generate Mindy report via Claude
    logger.info("Step 4/5: Generating Mindy report...")
    try:
        report = claude_client.generate_mindy_report(
            raw_data, vault_context, cfg.report_type, cfg
        )
        logger.info("Report length: %d chars", len(report))
    except NotImplementedError:
        report = (
            f"*Mindy here!* Report generation not yet implemented. "
            f"Raw data collected from {len(raw_data)} sources."
        )
        logger.info("[SKIP] generate_mindy_report not yet implemented — using placeholder")

    # 6. Archive report (non-fatal)
    try:
        archive_path = vault_writer.write_report_archive(cfg.report_type, report, cfg)
        if archive_path:
            logger.info("Archived report to %s", archive_path)
    except Exception as exc:
        logger.warning("Failed to archive report: %s", exc)

    # 7. Post to Slack
    logger.info("Step 5/5: Posting to Slack...")
    if cfg.dry_run:
        logger.info("[DRY RUN] Would post to Slack:")
        print("---")
        print(report[:500] + ("..." if len(report) > 500 else ""))
        print("---")
    else:
        ts = slack_poster.split_and_post(
            cfg.slack_channel_id, report, cfg.slack_bot_token
        )
        logger.info("Posted to Slack (ts=%s)", ts)

    logger.info("=== Done ===")


if __name__ == "__main__":
    main()
