---
description: Read a Linear issue and save its context for SpecKit workflow
---

# /linear.read - Read Linear issue for SpecKit

Read a Linear issue and prepare its context for the SpecKit workflow.

## Usage

```
/linear.read <ISSUE_ID>
```

**Example**: `/linear.read PDEV-156`

## How It Works

1. Fetch the issue from Linear
2. Display issue details
3. Save context for next steps
4. Suggest next command

## Instructions

### Step 1: Parse Issue ID

Extract the issue ID from arguments:
- Accept formats: `PDEV-156`, `156`, or full Linear URLs
- If no ID provided: ERROR "Please provide a Linear issue ID (e.g., PDEV-156)"

### Step 2: Fetch Issue from Linear

Use the Linear MCP tool:

```
mcp__linear-server__get_issue(issueId: "<ISSUE_ID>", includeRelations: true)
```

Extract from response:
- `identifier` (e.g., "PDEV-156")
- `title`
- `description`
- `url`
- `team.name` and `team.id`
- `project.name` and `project.id` (if present)
- `state.name`
- `assignee.name` and `assignee.email` (if present)
- `labels` (array of label names)
- `priority` (0-4)
- `dueDate` (if present)
- `createdAt`

### Step 3: Display Issue Summary

Show formatted output:

```markdown
# Linear Issue: <IDENTIFIER>

**Title**: <Title>
**URL**: <URL>

## Details

| Field | Value |
|-------|-------|
| Team | <Team Name> |
| Project | <Project Name> or _None_ |
| State | <State> |
| Assignee | <Name> (<Email>) or _Unassigned_ |
| Priority | <Priority Level> |
| Due Date | <Date> or _None_ |
| Created | <Date> |

## Labels

<If labels exist>
- `<label1>`
- `<label2>`
- `<label3>`

<If no labels>
_No labels_

## Description

<Full description from Linear, formatted as markdown>

<If no description>
_No description provided_

---

Issue loaded successfully.

**Next steps**:
1. Run `/speckit.specify` to create specification from this issue
2. Or manually copy the description above
```

### Step 4: Save Context

Save to `.specify/memory/linear-context.json`:

```json
{
  "issueId": "<ID>",
  "identifier": "<IDENTIFIER>",
  "title": "<Title>",
  "description": "<Description>",
  "url": "<URL>",
  "team": {
    "id": "<Team ID>",
    "name": "<Team Name>"
  },
  "project": {
    "id": "<Project ID>",
    "name": "<Project Name>"
  },
  "state": "<State>",
  "assignee": {
    "id": "<ID>",
    "name": "<Name>",
    "email": "<Email>"
  },
  "labels": ["label1", "label2"],
  "priority": 2,
  "dueDate": "<Date>",
  "readAt": "<Current timestamp>"
}
```

**Note**: This context can be used by `/linear.sync` later to link back to parent issue.

## Error Handling

| Error | Action |
|-------|--------|
| Issue not found | Show error: "Issue <ID> not found. Please verify the issue ID exists in Linear." |
| Invalid issue ID format | Show error: "Invalid issue ID format. Use format like PDEV-156" |
| API error | Show error: "Could not connect to Linear. Check your MCP server configuration." |
| Empty description | Show warning but continue: "This issue has no description" |

## Notes

- This command only reads, it doesn't modify anything
- Use this as the first step in the Linear -> SpecKit -> Linear workflow
- The description can be used directly with `/speckit.specify`
- Context is saved for later use by `/linear.sync`
