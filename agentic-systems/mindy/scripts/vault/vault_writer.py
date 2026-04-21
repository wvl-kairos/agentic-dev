"""Vault writer — writes/updates .md files in the vault."""

import logging
import re
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger("mindy.vault.writer")


def _slugify(name: str) -> str:
    """Convert a name to a filename slug. e.g. 'Rob Patrick' -> 'rob-patrick'."""
    slug = name.lower().strip()
    slug = re.sub(r"[áàäâã]", "a", slug)
    slug = re.sub(r"[éèëê]", "e", slug)
    slug = re.sub(r"[íìïî]", "i", slug)
    slug = re.sub(r"[óòöôõ]", "o", slug)
    slug = re.sub(r"[úùüû]", "u", slug)
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    return slug.strip("-")


def _write_file(path: Path, content: str) -> str:
    """Write content to a file, creating parent dirs if needed. Returns the path."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    logger.info("Wrote: %s (%d chars)", path, len(content))
    return str(path)


def write_sprint_file(vault_path: str, sprint_id: str, content: str) -> str:
    """Write a sprint file. sprint_id is like '2026-16' (YYYY-WW)."""
    path = Path(vault_path) / "sprints" / f"{sprint_id}.md"
    return _write_file(path, content)


def write_person_file(vault_path: str, name: str, content: str) -> str:
    """Write a person's profile file."""
    slug = _slugify(name)
    path = Path(vault_path) / "people" / f"{slug}.md"
    return _write_file(path, content)


def write_project_file(vault_path: str, name: str, content: str) -> str:
    """Write a project file. Name is the Linear project name, e.g. 'Order Visibility'."""
    slug = _slugify(name)
    path = Path(vault_path) / "projects" / f"{slug}.md"
    return _write_file(path, content)


def update_index(vault_path: str, content: str) -> str:
    """Update the vault index."""
    path = Path(vault_path) / "_index.md"
    return _write_file(path, content)


def write_report_archive(report_type: str, content: str, cfg) -> str:
    """Archive a report to vault/reports/YYYY-MM-DD-{type}.md."""
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    path = Path(cfg.vault_path) / "reports" / f"{today}-{report_type}.md"
    return _write_file(path, content)


def write_standup_notes(vault_path: str, sprint_id: str, content: str) -> str:
    """Write standup notes digest."""
    path = Path(vault_path) / "standup-notes" / f"{sprint_id}.md"
    return _write_file(path, content)


def write_decision(vault_path: str, title: str, content: str) -> str:
    """Write a decision document."""
    slug = _slugify(title)
    path = Path(vault_path) / "decisions" / f"{slug}.md"
    return _write_file(path, content)


def _get_current_sprint_id() -> str:
    """Get current sprint ID in YYYY-WW format."""
    now = datetime.now(timezone.utc)
    return f"{now.year}-{now.isocalendar()[1]:02d}"


def write_all(vault_updates: dict, cfg) -> list[str]:
    """Write all vault updates from Claude's compiled output.

    Expected vault_updates keys:
    - sprint_file: str (full .md content)
    - people_updates: dict {name: str_content}
    - projects_updates: dict {project_name: str_content}
    - index_update: str
    - standup_notes: str
    - new_decisions: list of {title, content}

    Returns list of written file paths.
    """
    if not vault_updates:
        return []

    vault_path = cfg.vault_path
    sprint_id = _get_current_sprint_id()
    written = []

    # Sprint file
    if vault_updates.get("sprint_file"):
        path = write_sprint_file(vault_path, sprint_id, vault_updates["sprint_file"])
        written.append(path)

    # People updates
    for name, content in (vault_updates.get("people_updates") or {}).items():
        if content:
            path = write_person_file(vault_path, name, content)
            written.append(path)

    # Project updates
    for name, content in (vault_updates.get("projects_updates") or {}).items():
        if content:
            path = write_project_file(vault_path, name, content)
            written.append(path)

    # Index
    if vault_updates.get("index_update"):
        path = update_index(vault_path, vault_updates["index_update"])
        written.append(path)

    # Standup notes
    if vault_updates.get("standup_notes"):
        path = write_standup_notes(vault_path, sprint_id, vault_updates["standup_notes"])
        written.append(path)

    # Decisions
    for decision in (vault_updates.get("new_decisions") or []):
        title = decision.get("title", "untitled")
        content = decision.get("content", "")
        if content:
            path = write_decision(vault_path, title, content)
            written.append(path)

    logger.info("write_all complete: %d files written", len(written))
    return written
