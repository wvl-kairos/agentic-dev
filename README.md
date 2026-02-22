# agentic-dev

Centralized monorepo for Claude Code plugins and agentic systems developed by the wvl-kairos org.

## Structure

```
agentic-dev/
├── plugins/                        # Claude Code plugins
│   ├── linear-plugin/              # Linear integration for Claude Code
│   └── multi-agent-code-review/    # Multi-agent code review plugin
└── agentic-systems/                # Future agentic system projects
```

## Plugins

### linear-plugin

Linear integration plugin for Claude Code. Provides commands to read Linear issues and sync SpecKit phases back as sub-issues.

- **Commands**: `linear.read`, `linear.sync`
- **Skills**: `linear-speckit-workflow`

### multi-agent-code-review

Multi-agent code review plugin that spawns specialized reviewers (frontend, backend, security, performance, testing) in parallel.

- **Agents**: Security, frontend, backend, performance, testing reviewers
- **Commands**: Code review orchestration
- **Hooks**: Pre/post review automation

## Getting Started

Each plugin has its own `README.md` with installation and usage instructions. Navigate to the relevant plugin directory for details.
