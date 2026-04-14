"""Tests for vault_reader and vault_writer."""

import os
import tempfile
from pathlib import Path

import pytest

from vault import vault_reader, vault_writer


@pytest.fixture
def vault_dir(tmp_path):
    """Create a temporary vault directory with seed data."""
    # Create structure
    (tmp_path / "sprints").mkdir()
    (tmp_path / "people").mkdir()
    (tmp_path / "projects").mkdir()
    (tmp_path / "decisions").mkdir()
    (tmp_path / "standup-notes").mkdir()
    (tmp_path / "reports").mkdir()

    # Seed files
    (tmp_path / "_index.md").write_text("# Kairos Index\nTest content")
    (tmp_path / "sprints" / "2026-14.md").write_text("# Sprint 14\nOldest sprint")
    (tmp_path / "sprints" / "2026-15.md").write_text("# Sprint 15\nRecent sprint")
    (tmp_path / "sprints" / "2026-16.md").write_text("# Sprint 16\nCurrent sprint")
    (tmp_path / "people" / "rob-patrick.md").write_text("# Rob Patrick\nEngineer")
    (tmp_path / "people" / "alex-maramaldo.md").write_text("# Alex Maramaldo\nData eng")
    (tmp_path / "projects" / "c1-schedule.md").write_text("# C1\nSchedule project")
    (tmp_path / "decisions" / "use-axon.md").write_text("# Use Axon\nDecision")

    return str(tmp_path)


# === vault_reader ===

class TestVaultReader:
    def test_read_index(self, vault_dir):
        content = vault_reader.read_index(vault_dir)
        assert "Kairos Index" in content

    def test_read_index_missing(self, tmp_path):
        assert vault_reader.read_index(str(tmp_path)) == ""

    def test_read_people_files(self, vault_dir):
        people = vault_reader.read_people_files(vault_dir)
        assert "rob-patrick" in people
        assert "alex-maramaldo" in people
        assert "Rob Patrick" in people["rob-patrick"]

    def test_read_people_empty(self, tmp_path):
        assert vault_reader.read_people_files(str(tmp_path)) == {}

    def test_read_sprint_history_default_4(self, vault_dir):
        sprints = vault_reader.read_sprint_history(vault_dir)
        assert len(sprints) == 3  # only 3 exist
        assert "Sprint 16" in sprints[0]  # most recent first

    def test_read_sprint_history_limit(self, vault_dir):
        sprints = vault_reader.read_sprint_history(vault_dir, last_n=2)
        assert len(sprints) == 2
        assert "Sprint 16" in sprints[0]
        assert "Sprint 15" in sprints[1]

    def test_read_project_files(self, vault_dir):
        projects = vault_reader.read_project_files(vault_dir)
        assert "c1-schedule" in projects

    def test_read_decision_files(self, vault_dir):
        decisions = vault_reader.read_decision_files(vault_dir)
        assert "use-axon" in decisions

    def test_build_context_bundle(self, vault_dir):
        class FakeCfg:
            vault_path = vault_dir

        bundle = vault_reader.build_context_bundle(FakeCfg())
        assert "=== VAULT INDEX ===" in bundle
        assert "=== RECENT SPRINTS" in bundle
        assert "=== TEAM PROFILES ===" in bundle
        assert "=== PROJECTS ===" in bundle
        assert "=== DECISIONS ===" in bundle
        assert "Rob Patrick" in bundle

    def test_build_context_bundle_empty_vault(self, tmp_path):
        class FakeCfg:
            vault_path = str(tmp_path)

        bundle = vault_reader.build_context_bundle(FakeCfg())
        assert bundle == ""


# === vault_writer ===

class TestVaultWriter:
    def test_slugify(self):
        assert vault_writer._slugify("Rob Patrick") == "rob-patrick"
        assert vault_writer._slugify("Tomás Palomo") == "tomas-palomo"
        assert vault_writer._slugify("Amanda Cunha") == "amanda-cunha"
        assert vault_writer._slugify("  Luis Suarez  ") == "luis-suarez"

    def test_write_sprint_file(self, tmp_path):
        path = vault_writer.write_sprint_file(str(tmp_path), "2026-16", "# Sprint 16")
        assert Path(path).exists()
        assert Path(path).read_text() == "# Sprint 16"
        assert "sprints/2026-16.md" in path

    def test_write_person_file(self, tmp_path):
        path = vault_writer.write_person_file(str(tmp_path), "Rob Patrick", "# Rob")
        assert Path(path).exists()
        assert "people/rob-patrick.md" in path

    def test_update_index(self, tmp_path):
        path = vault_writer.update_index(str(tmp_path), "# Updated Index")
        assert Path(path).read_text() == "# Updated Index"

    def test_write_report_archive(self, tmp_path):
        class FakeCfg:
            vault_path = str(tmp_path)

        path = vault_writer.write_report_archive("monday", "Report content", FakeCfg())
        assert Path(path).exists()
        assert "reports/" in path
        assert "-monday.md" in path

    def test_write_standup_notes(self, tmp_path):
        path = vault_writer.write_standup_notes(str(tmp_path), "2026-16", "Standup notes")
        assert Path(path).exists()
        assert "standup-notes/2026-16.md" in path

    def test_write_decision(self, tmp_path):
        path = vault_writer.write_decision(str(tmp_path), "Use Axon Framework", "Decision content")
        assert Path(path).exists()
        assert "decisions/use-axon-framework.md" in path

    def test_write_all(self, tmp_path):
        class FakeCfg:
            vault_path = str(tmp_path)

        vault_updates = {
            "sprint_file": "# Sprint 16\nContent",
            "people_updates": {
                "Rob Patrick": "# Rob\nEngineer",
                "Alex Maramaldo": "# Alex\nData",
            },
            "index_update": "# Updated Index",
            "standup_notes": "# Standup digest",
            "new_decisions": [
                {"title": "Adopt-Axon", "content": "# Axon decision"},
            ],
        }
        written = vault_writer.write_all(vault_updates, FakeCfg())

        assert len(written) == 6  # sprint + 2 people + index + standup + 1 decision
        for path in written:
            assert Path(path).exists()

    def test_write_all_empty(self, tmp_path):
        class FakeCfg:
            vault_path = str(tmp_path)

        written = vault_writer.write_all({}, FakeCfg())
        assert written == []

    def test_creates_parent_dirs(self, tmp_path):
        nested = tmp_path / "deep" / "nested"
        path = vault_writer.write_sprint_file(str(nested), "2026-16", "content")
        assert Path(path).exists()
