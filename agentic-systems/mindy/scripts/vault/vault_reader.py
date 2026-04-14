"""Vault reader — reads existing .md files to build context for Claude."""

import logging
import os
from pathlib import Path

logger = logging.getLogger("mindy.vault.reader")


def _read_file(path: Path) -> str:
    """Read a file and return its contents, or empty string if missing."""
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return ""


def read_index(vault_path: str) -> str:
    """Read vault/_index.md contents."""
    return _read_file(Path(vault_path) / "_index.md")


def read_people_files(vault_path: str) -> dict[str, str]:
    """Read all people .md files. Returns {filename_stem: content}."""
    people_dir = Path(vault_path) / "people"
    if not people_dir.exists():
        return {}

    result = {}
    for f in sorted(people_dir.glob("*.md")):
        result[f.stem] = f.read_text(encoding="utf-8")
    return result


def read_sprint_history(vault_path: str, last_n: int = 4) -> list[str]:
    """Read the last N sprint files, most recent first."""
    sprints_dir = Path(vault_path) / "sprints"
    if not sprints_dir.exists():
        return []

    files = sorted(sprints_dir.glob("*.md"), reverse=True)[:last_n]
    return [f.read_text(encoding="utf-8") for f in files]


def read_project_files(vault_path: str) -> dict[str, str]:
    """Read all project .md files. Returns {filename_stem: content}."""
    projects_dir = Path(vault_path) / "projects"
    if not projects_dir.exists():
        return {}

    result = {}
    for f in sorted(projects_dir.glob("*.md")):
        result[f.stem] = f.read_text(encoding="utf-8")
    return result


def read_decision_files(vault_path: str) -> dict[str, str]:
    """Read all decision .md files. Returns {filename_stem: content}."""
    decisions_dir = Path(vault_path) / "decisions"
    if not decisions_dir.exists():
        return {}

    result = {}
    for f in sorted(decisions_dir.glob("*.md")):
        result[f.stem] = f.read_text(encoding="utf-8")
    return result


def build_context_bundle(cfg) -> str:
    """Build a single context string from all vault files for Claude.

    Format:
    === VAULT INDEX ===
    {index}

    === RECENT SPRINTS (last 4) ===
    {sprints}

    === TEAM PROFILES ===
    {people}

    === PROJECTS ===
    {projects}

    === DECISIONS ===
    {decisions}
    """
    vault_path = cfg.vault_path
    sections = []

    # Index
    index = read_index(vault_path)
    if index:
        sections.append(f"=== VAULT INDEX ===\n{index}")

    # Recent sprints
    sprints = read_sprint_history(vault_path, last_n=4)
    if sprints:
        sprint_text = "\n\n---\n\n".join(sprints)
        sections.append(f"=== RECENT SPRINTS (last 4) ===\n{sprint_text}")

    # Team profiles
    people = read_people_files(vault_path)
    if people:
        people_text = "\n\n---\n\n".join(
            f"### {name}\n{content}" for name, content in people.items()
        )
        sections.append(f"=== TEAM PROFILES ===\n{people_text}")

    # Projects
    projects = read_project_files(vault_path)
    if projects:
        projects_text = "\n\n---\n\n".join(
            f"### {name}\n{content}" for name, content in projects.items()
        )
        sections.append(f"=== PROJECTS ===\n{projects_text}")

    # Decisions
    decisions = read_decision_files(vault_path)
    if decisions:
        decisions_text = "\n\n---\n\n".join(
            f"### {name}\n{content}" for name, content in decisions.items()
        )
        sections.append(f"=== DECISIONS ===\n{decisions_text}")

    bundle = "\n\n".join(sections)
    logger.info("Vault context bundle: %d chars, %d sections", len(bundle), len(sections))
    return bundle
