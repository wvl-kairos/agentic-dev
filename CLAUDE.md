# Multi-Agent Code Review System

This project uses a multi-agent code review system. Read these instructions to understand how it works.

## Available Agents

### review-orchestrator
The main coordinator. Use it for comprehensive reviews:
- Analyzes modified files
- Decides which specialized agents to activate
- Executes agents in parallel using the Task tool
- Consolidates findings

### Specialized Agents
- `frontend-reviewer`: React, Vue, CSS, accessibility, UX
- `backend-reviewer`: APIs, databases, architecture, error handling
- `security-reviewer`: OWASP, auth, injection, secrets
- `performance-reviewer`: Complexity, memory leaks, N+1, caching
- `testing-reviewer`: Coverage, test quality, edge cases

## Commands

- `/review` - Run full review
- `/review --agents security,performance` - Only specific agents
- `/review src/auth/*.ts` - Only specific files

## Quality Rules

### MUST DO
1. Always use review-orchestrator for complete reviews
2. Respect the confidence threshold (80 by default)
3. Prioritize issues: Critical > Warning > Suggestion
4. Include code examples in fixes

### NEVER DO
1. Don't review node_modules, dist, build, .git
2. Don't report issues with confidence < 80 (unless critical security)
3. Don't review unmodified files
4. Don't repeat the same issue multiple times

## Active Hooks

### PostToolUse (Edit|Write|MultiEdit)
Tracks modified files for auto-review.

### Stop
Triggers auto-review if files were modified since last review.

## Output Format

Findings should follow this JSON format to be parsed:

```json
{
  "category": "security|performance|frontend|backend|testing",
  "severity": "critical|warning|suggestion",
  "confidence": 85,
  "file": "src/path/to/file.ts",
  "line_start": 45,
  "line_end": 52,
  "title": "Brief issue title",
  "description": "Detailed description",
  "fix_example": "Example fix code"
}
```
