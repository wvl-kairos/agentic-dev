"""Shared fixtures for multi-agent-code-review tests."""

import sys
from pathlib import Path

import pytest

# Add scripts/utils to path so imports work
sys.path.insert(0, str(Path(__file__).parent.parent / 'utils'))


@pytest.fixture(autouse=True)
def isolate_file_tracker(tmp_path, monkeypatch):
    """Redirect all file_tracker state files to tmp_path to avoid side effects."""
    import file_tracker

    monkeypatch.setattr(file_tracker, 'LOG_DIR', tmp_path)
    monkeypatch.setattr(file_tracker, 'MODIFIED_FILES_LOG', tmp_path / 'modified_files.log')
    monkeypatch.setattr(file_tracker, 'REVIEW_STATE_FILE', tmp_path / 'review_state.json')
    monkeypatch.setattr(file_tracker, 'DEBUG_LOG_FILE', tmp_path / 'hooks_debug.log')
