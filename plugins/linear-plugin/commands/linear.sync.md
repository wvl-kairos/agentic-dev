---
description: Create Linear sub-issues from SpecKit phases, inheriting configuration from a parent issue
---

# /linear.sync - Create sub-issues from SpecKit phases

You are a project automation agent that creates Linear sub-issues for each **Phase** defined in SpecKit-generated tasks.

## Usage

```
/linear.sync <PARENT_ISSUE_ID>
```

**Example**: `/linear.sync PDEV-85`

## How It Works

1. **Fetch the parent issue** from Linear using the provided ID
2. **Inherit configuration** automatically:
   - Team (from parent)
   - Project (from parent)
   - Assignee (from parent, optional)
   - Labels (inherit relevant labels like `area:*`)
3. **Read SpecKit files**:
   - `tasks.md` for phases and task lists
   - `spec.md` for User Story details (acceptance scenarios, goals)
4. **Create one sub-issue per Phase** linked to the parent

## Instructions

### Step 1: Fetch Parent Issue

Use the Linear MCP tool to get the parent issue details:

```
mcp__linear-server__get_issue(issueId: "<PARENT_ISSUE_ID>", includeRelations: true)
```

Extract from the response:
- `team.id` -> Team for sub-issues
- `project.id` -> Project for sub-issues (if present)
- `assignee.id` -> (Optional) Assignee for sub-issues
- `labels` -> Inherit `area:*` labels if present
- `identifier` -> For referencing in descriptions
- `url` -> For parent issue link

### Step 2: Find and Parse Phases

Look for SpecKit files in these locations (in order):
1. `./tasks.md` and `./spec.md` (current directory)
2. `./specs/*/tasks.md` and `./specs/*/spec.md` (most recent feature)
3. Ask user for path if not found

**Parse the Phase structure from tasks.md**:

Phases are identified by headers like:
```markdown
## Phase 1: Setup (Shared Infrastructure)
## Phase 2: Foundational (Blocking Prerequisites)
## Phase 3: User Story 1 - Agent-to-Agent PR Review Initiation (Priority: P1)
## Phase 4: User Story 3 - Token Usage Guardrails (Priority: P1)
```

For each Phase, extract:
- Phase number (1, 2, 3...)
- Phase title (e.g., "Setup", "User Story 1 - Agent-to-Agent PR Review Initiation")
- Purpose/Goal (from the `**Purpose**:` or `**Goal**:` line under the phase header)
- Task count (number of `- [ ] T###` items)
- Task list (all tasks under that phase)
- Whether it's a User Story phase (contains "User Story" in title)

### Step 3: Enrich User Story Phases with spec.md

For phases that reference a User Story (e.g., "Phase 3: User Story 1 - ..."):

1. Read `spec.md` from the same directory
2. Find the matching User Story section (e.g., "### User Story 1 - ...")
3. Extract:
   - Full description paragraph
   - Priority and rationale (`**Why this priority**:`)
   - Independent Test description
   - Acceptance Scenarios (all `Given/When/Then` items)

### Step 4: Create Sub-Issues (One per Phase)

For each phase, create a Linear sub-issue using:

```
mcp__linear-server__create_issue(
  team: <inherited team ID or name>,
  project: <inherited project ID or name>,
  parentId: <parent issue ID>,
  title: "Phase <N>: <Phase Title>",
  description: <see templates below>,
  labels: <determine from phase type + inherited>,
  assignee: <inherited assignee if present>
)
```

#### Title Format
```
Phase 1: Setup (Shared Infrastructure)
Phase 3: User Story 1 - Agent-to-Agent PR Review Initiation
```

Keep titles concise - truncate if >100 characters and add "..." at the end.

#### Description Template: Infrastructure Phase (Non-User Story)

```markdown
## Purpose

<Purpose from tasks.md>

## Tasks (<N> total)

<List all tasks as checkboxes>
- [ ] T001 - <Task description>
- [ ] T002 - <Task description>
- [ ] T003 - <Task description>
...

## Notes

<Any special notes like "CRITICAL: No user story work can begin until this phase is complete">

---
Created via SpecKit -> Linear automation
```

#### Description Template: User Story Phase

```markdown
## Goal

<Goal from tasks.md phase header>

## User Story

<Full description from spec.md>

### Why This Priority

<Priority rationale from spec.md>

## Acceptance Scenarios

<All Given/When/Then scenarios from spec.md>

1. **Given** <condition>, **When** <action>, **Then** <result>
2. **Given** <condition>, **When** <action>, **Then** <result>
...

## Independent Test

<Independent test description from spec.md>

## Implementation Tasks (<N> total)

<List all tasks as checkboxes>
- [ ] T024 [US1] - <Task description>
- [ ] T025 [US1] - <Task description>
...

## Checkpoint

<Checkpoint description from tasks.md if present>

---
Created via SpecKit -> Linear automation
```

#### Label Assignment

Determine labels based on phase type:

| Phase Type | Add Label |
|------------|-----------|
| Setup, Infrastructure | `type:chore` |
| Foundational, Prerequisites | `type:chore` |
| User Story (P1) | `type:feature`, `priority:high` |
| User Story (P2) | `type:feature`, `priority:medium` |
| Polish, Cross-Cutting | `type:improvement` |

**Also inherit from parent**:
- All `area:*` labels
- All `priority:*` labels (unless phase has its own priority)

**IMPORTANT**:
- If a label doesn't exist in Linear, skip it silently and note in summary
- Use label names directly, not IDs (the MCP tool handles resolution)

### Step 5: Progress Feedback

Show progress while creating issues:

```
Fetching parent issue PDEV-85...

Found: "Adversarial PR Review"
-- Team: Product Development (PDEV)
-- Project: Agentic Acceleration
-- Assignee: armando.lopez@uplabs.us

Found tasks.md with 7 phases (96 tasks total) in specs/001-adversarial-pr-review/
Found spec.md with 4 User Stories

Creating sub-issues (one per phase)...
PDEV-86: Phase 1: Setup (Shared Infrastructure) - 8 tasks
PDEV-87: Phase 2: Foundational (Blocking Prerequisites) - 15 tasks
PDEV-88: Phase 3: User Story 1 - Agent-to-Agent PR Review Initiation - 14 tasks
PDEV-89: Phase 4: User Story 3 - Token Usage Guardrails - 13 tasks
PDEV-90: Phase 5: User Story 2 - Agent Negotiation and Iteration - 14 tasks
PDEV-91: Phase 6: User Story 4 - Human Reviewer Assignment from Linear - 14 tasks
PDEV-92: Phase 7: Polish & Cross-Cutting Concerns - 18 tasks
```

## Output Summary

After creating all issues, output:

```markdown
Created <N> phase sub-issues under <PARENT_IDENTIFIER>

**Configuration**:
-- Team: <Team Name>
-- Project: <Project Name>
-- Assignee: <Assignee Name>

**Sub-issues created**:
| Issue | Phase | Tasks | Type |
|-------|-------|-------|------|
| PDEV-86 | Phase 1: Setup | 8 | Infrastructure |
| PDEV-87 | Phase 2: Foundational | 15 | Infrastructure |
| PDEV-88 | Phase 3: US1 - PR Review Initiation | 14 | User Story (P1) |
| PDEV-89 | Phase 4: US3 - Token Guardrails | 13 | User Story (P1) |
| PDEV-90 | Phase 5: US2 - Agent Negotiation | 14 | User Story (P2) |
| PDEV-91 | Phase 6: US4 - Human Assignment | 14 | User Story (P2) |
| PDEV-92 | Phase 7: Polish | 18 | Improvement |

**Total**: 96 tasks across 7 phases

**View parent issue**: <parent URL>

---

**Next steps**:
- Review phase sub-issues in Linear
- Assign phases to team members
- Track progress by checking off tasks within each phase description
- Start with Phase 1, then Phase 2 (blocks all User Stories)
```

## Error Handling

| Error | Action |
|-------|--------|
| Parent issue not found | Show error: "Issue <ID> not found. Please verify the issue ID and try again." |
| No tasks.md found | Ask user: "Could not find tasks.md. Please provide the path to your tasks file." |
| No spec.md found | Warning: "spec.md not found. User Story phases will have limited detail." Continue without enrichment. |
| tasks.md has no phases | Show error: "No phases found in tasks.md. Ensure phases are defined with `## Phase N:` headers." |
| User Story not found in spec.md | Warning: "User Story X details not found in spec.md." Use tasks.md info only. |
| Label doesn't exist | Create issue without that label, list skipped labels in summary |
| API rate limit | Wait and retry with exponential backoff (1s, 2s, 4s, 8s) |
| Duplicate phase (same title exists) | Skip and note in summary |
| No team or project on parent | Ask user to specify team/project manually |

## Constraints

- **DO NOT** modify SpecKit files (tasks.md, spec.md, etc.)
- **DO NOT** generate implementation code
- **DO NOT** create issues without a valid parent
- **DO NOT** create issues if no phases found
- **DO NOT** create individual task issues (phases only)
- **DO** preserve phase ordering (Phase 1, 2, 3...)
- **DO** enrich User Story phases with spec.md details
- **DO** include full task lists in phase descriptions
- **DO** handle errors gracefully
- **DO** provide clear progress feedback

## Notes

- This command creates **one sub-issue per Phase**, not per task (tasks are too granular for Linear tracking)
- Task lists are included as checkboxes in the phase description for detailed tracking
- User Story phases are enriched with acceptance scenarios from spec.md
- Sub-issues remain linked to the parent for easy project management
- You can re-run this command to create issues for new phases (it will skip duplicates)
- Phase dependencies are noted in descriptions to guide execution order
