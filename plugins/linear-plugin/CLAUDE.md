# CLAUDE.md - Linear Plugin

This is a Claude Code plugin that provides Linear integration commands.

## Plugin Overview

Two slash commands for the Linear-SpecKit workflow:

- `/linear.read <ISSUE_ID>` - Read a Linear issue and prepare context for SpecKit
- `/linear.sync <PARENT_ISSUE_ID>` - Create sub-issues in Linear from SpecKit phases

## Architecture

### Commands
- `commands/linear.read.md` - Fetches issue from Linear MCP, displays formatted summary, saves context
- `commands/linear.sync.md` - Reads SpecKit artifacts (tasks.md, spec.md), creates one sub-issue per Phase in Linear

### Skills
- `skills/linear-speckit-workflow/` - End-to-end workflow orchestration

### MCP Configuration
- `.mcp.json` - Configures the Linear MCP server at `https://mcp.linear.app/mcp`

## Dependencies

- **Linear MCP Server**: Configured via `.mcp.json`, requires authentication via `/mcp`
- **SpecKit** (optional): For the full workflow pipeline (`specify init . --ai claude`)

## Workflow

```
/linear.read PDEV-156    ->  Read issue, save context
/speckit.specify          ->  Create spec.md
/speckit.plan             ->  Create plan.md
/speckit.tasks            ->  Create tasks.md
/linear.sync PDEV-156    ->  Push phases as sub-issues
```
