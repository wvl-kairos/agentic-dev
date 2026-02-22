# Linear Plugin for Claude Code

Linear integration plugin that provides slash commands for the Linear-SpecKit workflow.

## Installation

### Prerequisites

1. [Claude Code](https://claude.ai/code) CLI installed
2. Access to the `wvl-kairos` GitHub organization
3. `gh` CLI authenticated (recommended): `brew install gh && gh auth login`

### Step 1: Configure the marketplace (first time only)

All wvl-kairos plugins are registered in the `wvl-kairos-plugins` marketplace. If you already have it configured (e.g., you installed `multi-agent-code-review` before), skip to Step 2.

```bash
claude plugin marketplace add wvl-kairos/agentic-dev
```

> The marketplace registry lives in the `wvl-kairos/agentic-dev` monorepo. All wvl-kairos plugins are listed there.

### Step 2: Install the plugin

```bash
claude plugin install linear-plugin@wvl-kairos-plugins
```

> **Important:** The syntax is `plugin-name@marketplace-name` (use `@`, not `/`).

### Step 3: Verify the installation

```bash
claude plugin list
```

You should see `linear-plugin@wvl-kairos-plugins` with status `enabled`.

### Step 4: Start a new Claude Code session

Plugin commands are loaded at session start. Open a new session:

```bash
claude
```

## Authentication with Linear

### Linear MCP Server Setup

Connect Linear via MCP:

```bash
claude mcp add --transport http linear-server https://mcp.linear.app/mcp
```

This will prompt you to authenticate via your browser.

### Authenticate to Linear Workspace

Run the `/mcp` command inside Claude Code to authenticate with Linear. Make sure you are in the correct workspace before authenticating.

## Commands

### `/linear.read <ISSUE_ID>`

Read a Linear issue and prepare its context for the SpecKit workflow.

**Accepted formats:**
```
/linear.read PDEV-156
/linear.read 156
/linear.read https://linear.app/wvl-kairos/issue/PDEV-156
```

**What it does:**
- Fetches issue details from Linear (title, description, assignee, labels, relations)
- Displays a formatted summary in the terminal
- Saves context to `.specify/memory/linear-context.json` for SpecKit

### `/linear.sync <PARENT_ISSUE_ID>`

Create Linear sub-issues for each Phase defined in SpecKit tasks.

```
/linear.sync PDEV-156
```

**What it does:**
- Fetches the parent issue from Linear (inherits team, project, assignee, labels)
- Reads `tasks.md` to extract Phases (looks for `## Phase N: Title` headers)
- Reads `spec.md` to enrich User Story phases with acceptance scenarios
- Creates one sub-issue per Phase under the parent issue in Linear

## End-to-End Workflow

```
1. /linear.read PDEV-156        # Read issue from Linear
2. /speckit.specify              # Create spec.md from issue description
3. /speckit.plan                 # Create plan.md (implementation design)
4. /speckit.tasks                # Create tasks.md (task breakdown by phases)
5. /linear.sync PDEV-156         # Push phases back to Linear as sub-issues
```

## Optional: SpecKit

For the full workflow (steps 2-4), you need SpecKit installed:

```bash
uv tool install specify-cli --from git+https://github.com/github/spec-kit.git
```

The `/linear.read` and `/linear.sync` commands work independently of SpecKit.

## Updating the plugin

If a new version is available:

```bash
# Update marketplace cache
cd ~/.claude/plugins/marketplaces/wvl-kairos-plugins && git pull

# Reinstall
claude plugin uninstall linear-plugin@wvl-kairos-plugins
claude plugin install linear-plugin@wvl-kairos-plugins
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `not found in any configured marketplace` | Run Step 1 above, or update cache: `cd ~/.claude/plugins/marketplaces/wvl-kairos-plugins && git pull` |
| Old marketplace still points to `multi-agent-code-review` repo | Remove old marketplace and re-add: `claude plugin marketplace remove wvl-kairos-plugins && claude plugin marketplace add wvl-kairos/agentic-dev` |
| `Permission denied` during install | Ensure you have access to `wvl-kairos` GitHub org and run `gh auth login` |
| Commands don't appear after install | Start a **new** Claude Code session |
| Wrong install syntax | Use `@` not `/`: `linear-plugin@wvl-kairos-plugins` |
| "MCP server not found" | Run `/mcp` to connect, or restart your session |
| "Issue not found" | Verify the issue ID exists in your Linear workspace |
| "No tasks.md found" | Run `/speckit.tasks` first, or create `tasks.md` with `## Phase N: Title` headers |
| "No spec.md found" | Run `/speckit.specify` first |
