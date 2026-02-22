---
description: Run multi-agent code review on modified files. Spawns specialized reviewers (frontend, backend, security, performance, testing) in parallel.
argument-hint: "[--agents security,performance] [--threshold 80] [file patterns...]"
allowed-tools: Task, Read, Glob, Grep, Bash
---

# Multi-Agent Code Review

Run a comprehensive code review using specialized AI agents.

## Parse Arguments

Arguments: $ARGUMENTS

Extract from arguments:
- `--agents`: Comma-separated list of specific agents to use (default: auto-detect)
- `--threshold`: Confidence threshold 0-100 (default: 80)
- `--comment`: Post results as PR comment (if on a branch with PR)
- File patterns: Specific files/patterns to review (default: modified files)

## Execution Flow

### Step 1: Determine Files to Review

If file patterns provided in arguments, use those. Otherwise:

```bash
# Get modified files since last commit or PR base
MODIFIED=$(git diff --name-only HEAD~1 HEAD 2>/dev/null || git diff --name-only --cached || git status --porcelain | awk '{print $2}')

# Also check the hook's tracking log
if [ -f ".claude/hooks/modified_files.log" ]; then
  cat .claude/hooks/modified_files.log
fi

echo "$MODIFIED"
```

Filter out:
- `node_modules/`
- `dist/`, `build/`, `.next/`
- `*.min.js`, `*.bundle.js`
- `*.lock`, `package-lock.json`
- `.git/`
- Binary files

### Step 2: Invoke the Review Orchestrator

Use the `review-orchestrator` subagent to coordinate the review:

```
Use the review-orchestrator subagent to perform a comprehensive code review.

FILES TO REVIEW:
{list of files from Step 1}

CONFIGURATION:
- Agents to use: {from --agents or "auto-detect based on file types"}
- Confidence threshold: {from --threshold or 80}
- Output format: Markdown report

The orchestrator should:
1. Analyze file types
2. Spawn appropriate specialized reviewers in parallel
3. Collect and deduplicate findings
4. Filter by confidence threshold
5. Generate consolidated report
```

### Step 3: Handle Output

If `--comment` flag is present AND on a branch with open PR:
- Format findings as GitHub PR comment
- Post via gh CLI: `gh pr comment --body "..."`

Otherwise:
- Display formatted markdown report in terminal

## Quick Examples

```bash
# Review all modified files with auto-detection
/review

# Review only security and performance
/review --agents security,performance

# Review specific files
/review src/auth/*.ts src/api/users.ts

# With lower confidence threshold (more findings)
/review --threshold 60

# Post as PR comment
/review --comment
```

## Available Agents

| Agent | Specialization |
|-------|---------------|
| `frontend-reviewer` | React, Vue, CSS, accessibility |
| `backend-reviewer` | APIs, databases, architecture |
| `security-reviewer` | OWASP, auth, injection, secrets |
| `performance-reviewer` | Complexity, memory, caching |
| `testing-reviewer` | Coverage, test quality |

## Notes

- Review typically takes 30-120 seconds depending on file count
- Security issues are reported even below threshold if severity is "critical"
- Use `--agents` to speed up reviews when you know what you need
