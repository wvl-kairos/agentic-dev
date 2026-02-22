"""Tests for file_tracker.py — the core utility of the multi-agent code review plugin."""

import json

import pytest

from file_tracker import (
    should_ignore,
    add_modified_file,
    get_modified_files,
    clear_modified_files,
    classify_files,
    get_agents_for_files,
    get_files_for_agent,
    get_review_state,
    save_review_state,
    set_review_status,
    is_file_already_reviewed,
    should_track_file,
    should_auto_review,
    get_threshold,
    ReviewStatus,
    MODIFIED_FILES_LOG,
)


# ---------------------------------------------------------------------------
# should_ignore
# ---------------------------------------------------------------------------

class TestShouldIgnore:
    """Tests for the file-ignore logic."""

    def test_ignores_node_modules(self):
        assert should_ignore('src/node_modules/lodash/index.js') is True

    def test_ignores_dist(self):
        assert should_ignore('dist/bundle.js') is True

    def test_ignores_build_dir(self):
        assert should_ignore('build/output.js') is True

    def test_ignores_git_dir(self):
        assert should_ignore('.git/objects/abc') is True

    def test_ignores_pycache(self):
        assert should_ignore('src/__pycache__/module.cpython-311.pyc') is True

    def test_ignores_minified_js(self):
        assert should_ignore('vendor/lib.min.js') is True

    def test_ignores_bundle_js(self):
        assert should_ignore('static/app.bundle.js') is True

    def test_ignores_map_files(self):
        assert should_ignore('dist/app.js.map') is True

    def test_ignores_lockfiles(self):
        assert should_ignore('package-lock.json') is True
        assert should_ignore('yarn.lock') is True
        assert should_ignore('pnpm-lock.yaml') is True

    def test_ignores_pyc(self):
        assert should_ignore('module.pyc') is True

    def test_ignores_coverage(self):
        assert should_ignore('coverage/lcov-report/index.html') is True

    # --- .env* glob pattern (the bug fix) ---
    def test_ignores_env_bare(self):
        assert should_ignore('.env') is True

    def test_ignores_env_local(self):
        assert should_ignore('.env.local') is True

    def test_ignores_env_production(self):
        assert should_ignore('config/.env.production') is True

    def test_ignores_env_development(self):
        assert should_ignore('.env.development') is True

    # --- should NOT ignore ---
    def test_does_not_ignore_regular_source(self):
        assert should_ignore('src/components/Button.tsx') is False

    def test_does_not_ignore_python_source(self):
        assert should_ignore('src/utils/helpers.py') is False

    def test_does_not_ignore_readme(self):
        assert should_ignore('README.md') is False

    def test_case_insensitive(self):
        assert should_ignore('NODE_MODULES/lodash/index.js') is True


# ---------------------------------------------------------------------------
# add_modified_file / get_modified_files / clear_modified_files
# ---------------------------------------------------------------------------

class TestModifiedFiles:

    def test_add_and_get(self):
        add_modified_file('src/foo.ts')
        assert 'src/foo.ts' in get_modified_files()

    def test_add_returns_true_for_trackable(self):
        assert add_modified_file('src/foo.ts') is True

    def test_add_returns_false_for_ignored(self):
        assert add_modified_file('node_modules/lodash/index.js') is False

    def test_deduplicates(self):
        add_modified_file('src/foo.ts')
        add_modified_file('src/foo.ts')
        assert get_modified_files().count('src/foo.ts') == 1

    def test_empty_log_returns_empty(self):
        assert get_modified_files() == []

    def test_clear(self):
        add_modified_file('src/foo.ts')
        clear_modified_files()
        assert get_modified_files() == []

    def test_add_to_existing_empty_file(self, tmp_path):
        """If log file exists but is empty, adding a file should still work."""
        import file_tracker
        file_tracker.MODIFIED_FILES_LOG.write_text('')
        add_modified_file('src/bar.ts')
        assert get_modified_files() == ['src/bar.ts']


# ---------------------------------------------------------------------------
# ReviewStatus state machine
# ---------------------------------------------------------------------------

class TestReviewState:

    def test_default_state_is_idle(self):
        state = get_review_state()
        assert state['status'] == ReviewStatus.IDLE
        assert state['reviewed_files'] == []
        assert state['review_count'] == 0

    def test_corrupt_json_returns_idle(self, tmp_path):
        import file_tracker
        file_tracker.REVIEW_STATE_FILE.write_text('{ NOT VALID JSON')
        state = get_review_state()
        assert state['status'] == ReviewStatus.IDLE

    def test_set_reviewing_increments_count(self):
        set_review_status(ReviewStatus.REVIEWING, ['src/foo.ts'])
        state = get_review_state()
        assert state['status'] == ReviewStatus.REVIEWING
        assert state['review_count'] == 1
        assert 'src/foo.ts' in state['reviewed_files']
        assert state['session_id'] is not None

    def test_set_idle_resets_fields(self):
        set_review_status(ReviewStatus.REVIEWING, ['src/foo.ts'])
        set_review_status(ReviewStatus.IDLE)
        state = get_review_state()
        assert state['reviewed_files'] == []
        assert state['pending_files'] == []
        assert state['session_id'] is None

    def test_save_and_load_roundtrip(self):
        state = {'status': 'custom', 'review_count': 42, 'reviewed_files': ['a.py']}
        save_review_state(state)
        loaded = get_review_state()
        assert loaded['review_count'] == 42

    def test_is_file_already_reviewed(self):
        set_review_status(ReviewStatus.REVIEWING, ['src/foo.ts'])
        assert is_file_already_reviewed('src/foo.ts') is True
        assert is_file_already_reviewed('src/bar.ts') is False

    def test_is_file_not_reviewed_when_idle(self):
        assert is_file_already_reviewed('src/foo.ts') is False


# ---------------------------------------------------------------------------
# should_track_file
# ---------------------------------------------------------------------------

class TestShouldTrackFile:

    def test_ignores_node_modules(self):
        assert should_track_file('node_modules/x/y.js') is False

    def test_tracks_regular_file(self):
        assert should_track_file('src/app.ts') is True

    def test_skips_already_reviewed_during_fixing(self):
        set_review_status(ReviewStatus.REVIEWING, ['src/app.ts'])
        set_review_status(ReviewStatus.FIXING)
        assert should_track_file('src/app.ts') is False

    def test_tracks_new_file_during_fixing(self):
        set_review_status(ReviewStatus.REVIEWING, ['src/app.ts'])
        set_review_status(ReviewStatus.FIXING)
        assert should_track_file('src/new.ts') is True


# ---------------------------------------------------------------------------
# should_auto_review
# ---------------------------------------------------------------------------

class TestShouldAutoReview:

    def test_false_when_no_files(self):
        assert should_auto_review() is False

    def test_true_when_files_exist(self):
        add_modified_file('src/foo.ts')
        assert should_auto_review() is True

    def test_false_when_disabled(self, monkeypatch):
        add_modified_file('src/foo.ts')
        monkeypatch.setenv('AUTO_REVIEW_ENABLED', 'false')
        assert should_auto_review() is False

    def test_false_when_disabled_zero(self, monkeypatch):
        add_modified_file('src/foo.ts')
        monkeypatch.setenv('AUTO_REVIEW_ENABLED', '0')
        assert should_auto_review() is False


# ---------------------------------------------------------------------------
# get_threshold
# ---------------------------------------------------------------------------

class TestGetThreshold:

    def test_default_is_80(self, monkeypatch):
        monkeypatch.delenv('CODE_REVIEW_THRESHOLD', raising=False)
        assert get_threshold() == 80

    def test_reads_env(self, monkeypatch):
        monkeypatch.setenv('CODE_REVIEW_THRESHOLD', '90')
        assert get_threshold() == 90


# ---------------------------------------------------------------------------
# classify_files
# ---------------------------------------------------------------------------

class TestClassifyFiles:

    def test_tsx_classified_as_frontend(self):
        result = classify_files(['src/components/Button.tsx'])
        assert 'src/components/Button.tsx' in result['frontend']

    def test_auth_path_classified_as_security(self):
        result = classify_files(['src/auth/login.ts'])
        assert 'src/auth/login.ts' in result['security']

    def test_test_file_classified_as_testing(self):
        result = classify_files(['src/utils/helpers.test.ts'])
        assert 'src/utils/helpers.test.ts' in result['testing']
        # Test files should not leak into other categories
        assert 'src/utils/helpers.test.ts' not in result['backend']

    def test_spec_file_classified_as_testing(self):
        result = classify_files(['src/App.spec.tsx'])
        assert 'src/App.spec.tsx' in result['testing']

    def test_tests_directory_classified_as_testing(self):
        result = classify_files(['src/tests/login.ts'])
        assert 'src/tests/login.ts' in result['testing']

    def test_empty_list(self):
        result = classify_files([])
        assert all(len(v) == 0 for v in result.values())

    def test_api_path_classified_as_backend(self):
        result = classify_files(['src/api/users.ts'])
        assert 'src/api/users.ts' in result['backend']

    def test_sql_classified_as_backend_security_performance(self):
        result = classify_files(['db/migrations/001.sql'])
        assert 'db/migrations/001.sql' in result['backend']
        assert 'db/migrations/001.sql' in result['security']
        assert 'db/migrations/001.sql' in result['performance']

    def test_css_classified_as_frontend(self):
        result = classify_files(['src/styles/app.css'])
        assert 'src/styles/app.css' in result['frontend']

    def test_github_actions_classified_as_config_and_security(self):
        result = classify_files(['.github/workflows/ci.yml'])
        assert '.github/workflows/ci.yml' in result['config']
        assert '.github/workflows/ci.yml' in result['security']

    def test_json_config_classified_as_config(self):
        result = classify_files(['tsconfig.json'])
        assert 'tsconfig.json' in result['config']

    def test_generic_py_classified_as_backend(self):
        result = classify_files(['src/utils/helpers.py'])
        assert 'src/utils/helpers.py' in result['backend']

    def test_no_false_positive_test_in_directory_name(self):
        """A file in a dir containing 'test' as substring should not be classified as testing."""
        result = classify_files(['src/services/userTests/login.ts'])
        assert 'src/services/userTests/login.ts' not in result['testing']


# ---------------------------------------------------------------------------
# get_agents_for_files / get_files_for_agent
# ---------------------------------------------------------------------------

class TestAgentSelection:

    def test_frontend_files_select_frontend_reviewer(self):
        agents = get_agents_for_files(['src/App.tsx'])
        assert 'frontend-reviewer' in agents

    def test_security_files_select_security_reviewer(self):
        agents = get_agents_for_files(['src/auth/login.ts'])
        assert 'security-reviewer' in agents

    def test_code_files_always_include_testing_reviewer(self):
        agents = get_agents_for_files(['src/utils/helpers.py'])
        assert 'testing-reviewer' in agents

    def test_empty_files_no_agents(self):
        agents = get_agents_for_files([])
        assert len(agents) == 0

    def test_get_files_for_frontend_reviewer(self):
        files = ['src/App.tsx', 'src/api/users.ts']
        result = get_files_for_agent(files, 'frontend-reviewer')
        assert 'src/App.tsx' in result
        assert 'src/api/users.ts' not in result

    def test_get_files_for_unknown_agent_returns_all(self):
        files = ['src/App.tsx']
        result = get_files_for_agent(files, 'unknown-agent')
        assert result == files
