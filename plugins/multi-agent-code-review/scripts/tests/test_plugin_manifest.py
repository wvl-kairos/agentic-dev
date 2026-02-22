"""Tests for plugin manifest integrity — verifies plugin.json declarations match actual files."""

import json
from pathlib import Path

PLUGIN_ROOT = Path(__file__).parent.parent.parent  # multi-agent-code-review/
MONOREPO_ROOT = PLUGIN_ROOT.parent.parent  # agentic-dev/


class TestPluginManifest:

    def setup_method(self):
        self.manifest = json.loads(
            (PLUGIN_ROOT / '.claude-plugin' / 'plugin.json').read_text()
        )

    def test_agent_paths_exist(self):
        for agent_path in self.manifest.get('agents', []):
            resolved = PLUGIN_ROOT / agent_path
            assert resolved.exists(), f"Agent file missing: {agent_path}"

    def test_commands_dir_exists(self):
        commands_dir = PLUGIN_ROOT / self.manifest['commands'].lstrip('./')
        assert commands_dir.is_dir(), f"Commands dir missing: {self.manifest['commands']}"

    def test_skills_dir_exists(self):
        skills_dir = PLUGIN_ROOT / self.manifest['skills'].lstrip('./')
        assert skills_dir.is_dir(), f"Skills dir missing: {self.manifest['skills']}"

    def test_required_fields_present(self):
        for field in ['name', 'version', 'description', 'commands']:
            assert field in self.manifest, f"Required field missing: {field}"


class TestMarketplaceManifest:

    def setup_method(self):
        self.marketplace = json.loads(
            (MONOREPO_ROOT / '.claude-plugin' / 'marketplace.json').read_text()
        )
        self.plugin = json.loads(
            (PLUGIN_ROOT / '.claude-plugin' / 'plugin.json').read_text()
        )

    def test_plugin_listed_in_marketplace(self):
        names = [p['name'] for p in self.marketplace['plugins']]
        assert self.plugin['name'] in names

    def test_versions_match(self):
        entry = next(
            p for p in self.marketplace['plugins']
            if p['name'] == self.plugin['name']
        )
        assert entry['version'] == self.plugin['version'], (
            f"Version mismatch: marketplace={entry['version']}, plugin={self.plugin['version']}"
        )

    def test_source_is_relative_path(self):
        """Verify sources use relative paths for monorepo layout."""
        for plugin in self.marketplace['plugins']:
            source = plugin['source']
            assert isinstance(source, str), (
                f"Plugin {plugin['name']} source should be a relative path string"
            )
            assert source.startswith('./'), (
                f"Plugin {plugin['name']} source should start with './'"
            )

    def test_source_paths_resolve_to_plugin_dirs(self):
        """Verify each source path actually contains a plugin.json."""
        for plugin in self.marketplace['plugins']:
            plugin_dir = MONOREPO_ROOT / plugin['source']
            manifest = plugin_dir / '.claude-plugin' / 'plugin.json'
            assert manifest.exists(), (
                f"Plugin {plugin['name']} source path {plugin['source']} "
                f"does not contain .claude-plugin/plugin.json"
            )
