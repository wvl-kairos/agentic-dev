"""Tests for check-pending-review.py — the UserPromptSubmit hook."""

import importlib.util
from pathlib import Path

# check-pending-review.py has a hyphen, so we use importlib to load it
_spec = importlib.util.spec_from_file_location(
    "check_pending_review", Path(__file__).parent.parent / "check-pending-review.py"
)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)
generate_review_prompt = _mod.generate_review_prompt


class TestGenerateReviewPrompt:

    def test_contains_file_names(self):
        files = ['src/auth/login.ts', 'src/api/users.ts']
        agents = {'security-reviewer', 'backend-reviewer'}
        output = generate_review_prompt(files, agents, threshold=80)
        assert 'src/auth/login.ts' in output
        assert 'src/api/users.ts' in output

    def test_contains_agent_names(self):
        agents = {'security-reviewer', 'testing-reviewer'}
        output = generate_review_prompt(['src/foo.ts'], agents, threshold=80)
        assert 'security-reviewer' in output
        assert 'testing-reviewer' in output

    def test_contains_threshold(self):
        output = generate_review_prompt(['src/foo.ts'], {'backend-reviewer'}, threshold=90)
        assert '90' in output

    def test_wraps_in_xml_tag(self):
        output = generate_review_prompt(['src/foo.ts'], {'backend-reviewer'}, threshold=80)
        assert '<auto-review-triggered>' in output
        assert '</auto-review-triggered>' in output

    def test_empty_files_does_not_raise(self):
        output = generate_review_prompt([], set(), threshold=80)
        assert isinstance(output, str)
