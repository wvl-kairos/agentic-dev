# Multi-Agent Code Review Plugin

An automated multi-agent code review system for Claude Code. Orchestrates 5 specialized AI reviewers running in parallel to provide comprehensive code analysis.

## Features

- **5 Specialized Reviewers**: Security, Frontend, Backend, Performance, Testing
- **Parallel Execution**: All agents run simultaneously for fast reviews
- **Smart File Detection**: Automatically determines which reviewers to activate based on file types
- **Confidence Scoring**: Filters false positives with configurable threshold (default: 80)
- **Auto Review**: Hooks trigger automatic reviews when you finish working
- **Manual Review**: `/review` command for on-demand analysis

## Installation

### Prerequisites

1. [Claude Code](https://claude.ai/code) CLI installed
2. Access to the `wvl-kairos` GitHub organization
3. Python >= 3.8

### From Marketplace (Recommended)

```bash
# Step 1: Add the wvl-kairos marketplace (one-time setup)
claude plugin marketplace add wvl-kairos/agentic-dev

# Step 2: Install the plugin
claude plugin install multi-agent-code-review@wvl-kairos-plugins
```

> **Note:** The syntax is `plugin-name@marketplace-name` (use `@`, not `/`).

After installing, **start a new Claude Code session** for the hooks and commands to load.

## Directory Structure

```
multi-agent-code-review/
├── .claude-plugin/
│   └── plugin.json           # Plugin manifest
├── agents/
│   ├── review-orchestrator.md
│   ├── security-reviewer.md
│   ├── frontend-reviewer.md
│   ├── backend-reviewer.md
│   ├── performance-reviewer.md
│   └── testing-reviewer.md
├── commands/
│   └── review.md             # /review command
├── skills/
│   └── code-review-patterns/
│       └── SKILL.md
├── scripts/
│   ├── track-modified-files.py
│   ├── auto-review.py
│   └── utils/
│       └── file_tracker.py
├── hooks/
│   └── hooks.json            # Hook configuration
├── CLAUDE.md
└── README.md
```

## Usage

### Automatic Review

Reviews run automatically when Claude finishes working (Stop hook). The hook uses **exit code 2** which forces Claude to continue working and execute the review.

**How it works:**
1. You modify files with Claude's help
2. When Claude finishes responding, the Stop hook checks for modified files
3. If files exist, it outputs review instructions to stderr and exits with code 2
4. Claude receives the instructions and spawns specialized reviewers in parallel
5. You get a consolidated report with all findings

Only activates if files were modified since the last review.

### Manual Review

```bash
# Review all modified files
/review

# Review with specific agents only
/review --agents security,performance

# Review specific files
/review src/auth/*.ts

# Review with different confidence threshold
/review --threshold 70
```

### Invoke Specific Agents

```bash
# Security-focused review
> Use the security-reviewer agent to check my authentication code

# Full orchestrated review
> Use the review-orchestrator to do a comprehensive review of my changes
```

## Specialized Reviewers

| Agent | Model | Focus Areas |
|-------|-------|-------------|
| **security-reviewer** | Sonnet | OWASP Top 10, injection, auth, secrets, XSS/CSRF |
| **frontend-reviewer** | Haiku | React/Vue, accessibility, CSS, hooks, state |
| **backend-reviewer** | Haiku | APIs, databases, architecture, error handling |
| **performance-reviewer** | Haiku | N+1 queries, memory leaks, O(n²), caching |
| **testing-reviewer** | Haiku | Coverage, test quality, edge cases, mocking |

## Smart File Classification

The system automatically determines which reviewers to activate:

| File Type | Reviewers Activated |
|-----------|---------------------|
| `.tsx`, `.jsx`, `.vue`, `.css` | frontend, performance |
| `/api/`, `/server/`, `.ts`, `.js` | backend, performance |
| `/auth/`, `/login/`, `.env` | security, backend |
| `.test.ts`, `.spec.js` | testing |
| `.sql`, `.graphql`, `.prisma` | backend, security, performance |
| `Dockerfile`, CI/CD configs | security, backend |
| `.json`, `.yaml` configs | backend |

## Configuration

### Auto vs Manual Review

| Mode | How to Enable |
|------|---------------|
| **Auto** (default) | `AUTO_REVIEW_ENABLED=true` + Stop hook active |
| **Manual only** | `AUTO_REVIEW_ENABLED=false` or remove Stop hook |
| **Hybrid** | Auto enabled, but run `/review` anytime for on-demand review |

**To disable auto-review per session:**
```bash
export AUTO_REVIEW_ENABLED=false
claude
```

**To disable auto-review permanently**, edit your `.claude/settings.json` and remove the Stop hook section (keep PostToolUse so `/review` knows which files to check).

### Environment Variables

```bash
# Confidence threshold (default: 80)
export CODE_REVIEW_THRESHOLD=80

# Enable/disable auto-review (default: true)
export AUTO_REVIEW_ENABLED=true

# Include performance reviewer (default: true)
export INCLUDE_PERFORMANCE_REVIEW=true
```

### Customize Review Rules

Edit `skills/code-review-patterns/SKILL.md` to add project-specific rules.

## Report Format

```markdown
## Code Review Report

### Summary
| Metric | Count |
|--------|-------|
| Files reviewed | 12 |
| Critical issues | 2 |
| Warnings | 5 |
| Suggestions | 8 |

### Critical Issues (Must Fix)

#### [Security] SQL Injection Risk
**File**: `src/api/users.ts:45`
**Confidence**: 95%

User input concatenated directly into SQL query.

**Fix**:
```typescript
const query = `SELECT * FROM users WHERE id = $1`;
const result = await db.query(query, [userId]);
```

### Warnings (Should Fix)
...

### Suggestions (Consider)
...
```

## Architecture

```
┌─────────────────────┐
│   Stop Hook         │
│   (auto-review.py)  │
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│ Review Orchestrator │
└─────────┬───────────┘
          │
          ▼
┌─────────────────────────────────────────┐
│         Parallel Execution              │
│  ┌────────┐ ┌────────┐ ┌────────┐      │
│  │Security│ │Frontend│ │Backend │ ...  │
│  └────┬───┘ └────┬───┘ └────┬───┘      │
│       │          │          │           │
└───────┴──────────┴──────────┴───────────┘
                   │
                   ▼
        ┌─────────────────────┐
        │   Consolidated      │
        │   Report            │
        └─────────────────────┘
```

## Troubleshooting

### Auto-review not triggering?

1. **Check if files are being tracked:**
   ```bash
   cat .claude/hooks/modified_files.log
   ```

2. **Check the debug log:**
   ```bash
   cat .claude/hooks/auto_review_debug.log
   ```

3. **Verify hooks are loaded:**
   Look for "Running PostToolUse hooks…" and "Running Stop hooks…" messages in Claude's output.

4. **Test the script manually:**
   ```bash
   python3 ~/.claude/plugins/cache/wvl-kairos-plugins/multi-agent-code-review/1.0.0/scripts/auto-review.py
   echo "Exit code: $?"
   ```
   Should output review instructions and exit with code 2.

### Common issues

- **Files in `test_*` directories classified as tests**: Fixed in v1.0.0 - only checks filename patterns, not full path
- **Review loops**: The system tracks review state to prevent infinite loops
- **Exit code 2**: This is intentional - it forces Claude to continue working

## Troubleshooting (additional)

| Issue | Solution |
|-------|----------|
| `not found in any configured marketplace` | Update marketplace cache: `cd ~/.claude/plugins/marketplaces/wvl-kairos-plugins && git pull`. If still fails, re-add: `claude plugin marketplace remove wvl-kairos-plugins && claude plugin marketplace add wvl-kairos/agentic-dev` |
| Commands don't appear after install | Start a **new** Claude Code session |
| Wrong install syntax error | Use `@` not `/`: `multi-agent-code-review@wvl-kairos-plugins` |

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/new-reviewer`)
3. Commit your changes (`git commit -am 'Add accessibility reviewer'`)
4. Push to the branch (`git push origin feature/new-reviewer`)
5. Create a Pull Request

## License

MIT License - see [LICENSE](LICENSE) for details.
