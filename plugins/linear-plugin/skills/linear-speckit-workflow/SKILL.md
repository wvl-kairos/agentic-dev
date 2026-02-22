---
name: linear-speckit-workflow
description: End-to-end workflow that reads a Linear issue, runs it through SpecKit (specify, plan, tasks), and syncs phases back as sub-issues. Use when someone asks to break down a Linear issue into sub-issues, create a spec from a Linear issue, or run the full Linear-to-SpecKit pipeline.
---

# Linear-SpecKit Workflow

Automates the full pipeline from Linear issue to structured sub-issues via SpecKit.

## Overview

This skill orchestrates the complete workflow:
1. Reading a Linear issue for context
2. Running SpecKit to create specifications, plans, and task breakdowns
3. Syncing the resulting phases back to Linear as sub-issues

## Usage

### Full Pipeline

```
Run the Linear-SpecKit workflow for PDEV-156
```

### Individual Steps

```
/linear.read PDEV-156        # Step 1: Read issue from Linear
/speckit.specify              # Step 2: Create spec.md from issue description
/speckit.plan                 # Step 3: Create plan.md (implementation design)
/speckit.tasks                # Step 4: Create tasks.md (task breakdown)
/linear.sync PDEV-156         # Step 5: Push phases back to Linear as sub-issues
```

## Workflow Diagram

```
Linear Issue  -->  SpecKit Artifacts  -->  Linear Sub-issues
     |                    |                       |
/linear.read       /speckit.specify         /linear.sync
                   /speckit.plan
                   /speckit.tasks
```

## Prerequisites

- Linear MCP server authenticated (run `/mcp` then authenticate with Linear workspace)
- SpecKit installed (`uv tool install specify-cli --from git+https://github.com/github/spec-kit.git`)
- SpecKit initialized in the repo (`specify init . --ai claude`)

## Linear MCP Setup

Connect Linear via MCP:

```
claude mcp add --transport sse linear-server https://mcp.linear.app/sse
```

Then authenticate:

```
Run /mcp command to authenticate with Linear (must be in the correct workspace)
```

## File Structure

After running the workflow:

```
project/
├── .specify/
│   └── memory/
│       └── linear-context.json   # Saved Linear issue context
└── specs/
    └── <feature>/
        ├── spec.md               # Feature specification
        ├── plan.md               # Implementation plan
        └── tasks.md              # Task breakdown by phase
```

## Related Commands

- `/linear.read` - Read a Linear issue and save context
- `/linear.sync` - Create sub-issues from SpecKit phases
