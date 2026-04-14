# Mindy — Weekly Team Intelligence System
## Architecture Spec for Claude Code

---

## Overview

Automated twice-weekly reporting system for the Kairos team. On a cron schedule, a Python orchestrator collects data from five sources, uses Claude Sonnet to update a living Obsidian-style wiki vault, generates a Mindy report in Slack format, and posts it to `#meeting-summaries`. The vault is stored as a GitHub repo and committed back on every run.

---

## Repository structure

```
wvl-kairos-vault/               ← new dedicated GitHub repo
├── .github/
│   └── workflows/
│       ├── monday-report.yml
│       └── friday-report.yml
├── scripts/
│   ├── orchestrator.py         ← main entrypoint
│   ├── collectors/
│   │   ├── linear_collector.py
│   │   ├── fireflies_collector.py
│   │   ├── github_collector.py
│   │   ├── notion_collector.py
│   │   └── slack_collector.py
│   ├── vault/
│   │   ├── vault_reader.py     ← reads existing .md files for context
│   │   └── vault_writer.py     ← writes/updates .md files
│   ├── claude_client.py        ← Anthropic API wrapper
│   ├── slack_poster.py         ← Slack Web API wrapper
│   └── config.py               ← constants and env var loader
├── vault/
│   ├── _index.md               ← master index (auto-maintained by Claude)
│   ├── sprints/                ← one .md per sprint cycle
│   │   └── YYYY-WW.md
│   ├── people/                 ← one .md per team member
│   │   ├── rob-patrick.md
│   │   ├── alex-maramaldo.md
│   │   ├── antwoine-flowers.md
│   │   ├── tomas-palomo.md
│   │   ├── armando-lopez.md
│   │   ├── evandro-machado.md
│   │   ├── amanda-cunha.md
│   │   └── sunny-chalam.md
│   ├── projects/               ← one .md per Linear project
│   ├── decisions/              ← key architectural/product decisions
│   ├── standup-notes/          ← weekly digest from Fireflies
│   └── reports/                ← archive of all posted Slack reports
│       └── YYYY-MM-DD-monday.md
└── requirements.txt
```

---

## GitHub Actions workflows

### `.github/workflows/monday-report.yml`

```yaml
name: Monday Kickoff Report
on:
  schedule:
    - cron: '0 14 * * 1'   # Monday 14:00 UTC = 08:00 CST
  workflow_dispatch:
    inputs:
      dry_run:
        description: 'Dry run (no Slack post, no vault commit)'
        type: boolean
        default: false

permissions:
  contents: write

jobs:
  monday-report:
    runs-on: ubuntu-latest
    timeout-minutes: 20
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 1

      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
          cache: pip

      - run: pip install -r requirements.txt

      - name: Run Monday orchestrator
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
          LINEAR_API_KEY: ${{ secrets.LINEAR_API_KEY }}
          FIREFLIES_API_KEY: ${{ secrets.FIREFLIES_API_KEY }}
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          SLACK_BOT_TOKEN: ${{ secrets.SLACK_BOT_TOKEN }}
          NOTION_TOKEN: ${{ secrets.NOTION_TOKEN }}
          SLACK_CHANNEL_ID: C0AB0GUBX3K
          REPORT_TYPE: monday
          DRY_RUN: ${{ github.event.inputs.dry_run || 'false' }}
        run: python scripts/orchestrator.py

      - name: Commit vault updates
        if: ${{ github.event.inputs.dry_run != 'true' }}
        run: |
          git config user.name "mindy[bot]"
          git config user.email "mindy-bot@uplabs.us"
          git add -A
          git diff --staged --quiet || git commit -m "vault: monday sync $(date -u +%Y-%m-%d) [skip ci]"
          git push
```

### `.github/workflows/friday-report.yml`

Same structure, with:
- `cron: '0 21 * * 5'`  (Friday 21:00 UTC = 15:00 CST)
- `REPORT_TYPE: friday`

---

## Python implementation

### `scripts/config.py`

```python
import os
from dataclasses import dataclass

@dataclass
class Config:
    anthropic_api_key: str
    linear_api_key: str
    fireflies_api_key: str
    github_token: str
    slack_bot_token: str
    notion_token: str
    slack_channel_id: str
    report_type: str         # "monday" | "friday"
    dry_run: bool

    # Kairos constants
    linear_team_id: str = "b4298b9c-8de9-427c-bee5-40c1ceba483f"
    linear_workspace: str = "wvl-kairos"
    github_org: str = "wvl-kairos"
    github_repo: str = "kairos"
    fireflies_organizer: str = "sunny.chalam@uplabs.us"
    notion_merges_db: str = "30a4f5abefac80f39bd7d2c67a970383"
    notion_merge_docs_url: str = "https://www.notion.so/30a4f5abefac80f39bd7d2c67a970383?v=30a4f5abefac80e3ba44000c7655213d"
    vault_path: str = "vault"
    claude_model: str = "claude-sonnet-4-20250514"

    team_members: list = None

    def __post_init__(self):
        self.team_members = [
            "Rob Patrick", "Alex Maramaldo", "Antwoine Flowers",
            "Tomás Palomo", "Armando Lopez", "Evandro Machado",
            "Amanda Cunha", "Sunny Chalam"
        ]

def load_config() -> Config:
    return Config(
        anthropic_api_key=os.environ["ANTHROPIC_API_KEY"],
        linear_api_key=os.environ["LINEAR_API_KEY"],
        fireflies_api_key=os.environ["FIREFLIES_API_KEY"],
        github_token=os.environ["GITHUB_TOKEN"],
        slack_bot_token=os.environ["SLACK_BOT_TOKEN"],
        notion_token=os.environ["NOTION_TOKEN"],
        slack_channel_id=os.environ.get("SLACK_CHANNEL_ID", "C0AB0GUBX3K"),
        report_type=os.environ.get("REPORT_TYPE", "monday"),
        dry_run=os.environ.get("DRY_RUN", "false").lower() == "true",
    )
```

---

### `scripts/collectors/linear_collector.py`

Calls the Linear GraphQL API to collect:

```python
"""
Queries to implement:

1. current_cycle() → {id, name, startsAt, endsAt, number}
   GraphQL: team(id: TEAM_ID).activeCycle

2. completed_this_week() → list of issues
   Filter: updatedAt > 7 days ago, state.type = "completed"
   Fields per issue: id, identifier, title, assignee.name, project.name, completedAt

3. in_progress() → list of issues
   Filter: state.type in ["started", "unstarted"] and assignee != null
   Fields: id, identifier, title, assignee.name, state.name, project.name

4. ready_for_dev() → list of issues
   Filter: state.name = "Ready for Dev"
   Same fields

Return: CollectedData dataclass with all four lists
"""
```

**Implementation notes:**
- Use `httpx` for async HTTP, or `requests` for simplicity
- Linear GraphQL endpoint: `https://api.linear.app/graphql`
- Auth header: `Authorization: Bearer {LINEAR_API_KEY}`
- Paginate with `after` cursor if needed (unlikely for weekly window)

---

### `scripts/collectors/fireflies_collector.py`

Calls the Fireflies GraphQL API:

```python
"""
Queries to implement:

1. get_standups_this_week() → list of transcripts
   Filter: fromDate = 7 days ago, organizer_email = "sunny.chalam@uplabs.us"
   Fields per transcript: id, title, date, participants, summary.action_items, summary.overview

Return: list of StandupNote(date, participants, action_items, overview)
"""
```

- Fireflies GraphQL endpoint: `https://api.fireflies.ai/graphql`
- Auth header: `Authorization: Bearer {FIREFLIES_API_KEY}`

---

### `scripts/collectors/github_collector.py`

Uses the GitHub REST API via `PyGithub` or raw `requests`:

```python
"""
Functions to implement:

1. get_merged_prs_this_week(repo="wvl-kairos/kairos") → list of PRs
   Filter: merged_at > 7 days ago, base_branch = "develop"
   Fields: number, title, author, merged_at, body (first 200 chars)

2. get_commit_authors_this_week(repo) → dict {author: commit_count}
   For detecting team members with low Linear activity

Return: MergedPRs(prs=list, authors_by_count=dict)
"""
```

- Use `GITHUB_TOKEN` from env (already available in Actions)
- Endpoint: `https://api.github.com`

---

### `scripts/collectors/notion_collector.py`

```python
"""
Functions to implement:

1. get_recent_merge_docs(days=7) → list of pages
   Database: 30a4f5abefac80f39bd7d2c67a970383
   Filter: created_time > 7 days ago
   Fields: title, url, created_time, properties

Return: list of MergeDoc(title, url, created_at)
"""
```

- Notion API: `https://api.notion.com/v1`
- Auth: `Authorization: Bearer {NOTION_TOKEN}`, `Notion-Version: 2022-06-28`

---

### `scripts/collectors/slack_collector.py`

```python
"""
Functions to implement:

1. get_recent_channel_messages(channel_id, days=7) → list of messages
   Used for context only — helps Claude detect tone, open items

Return: list of SlackMessage(ts, user, text)
Note: use Slack Web API conversations.history
"""
```

---

### `scripts/vault/vault_reader.py`

```python
"""
Functions:

1. read_index() → str (contents of vault/_index.md)
2. read_people_files() → dict {name: str_content}
3. read_sprint_history(last_n=4) → list of str (last N sprint files)
4. read_project_files() → dict {project_name: str_content}
5. build_context_bundle(cfg) → str
   Concatenates all relevant vault content into a single string
   to pass as context to Claude.
   
   Format:
   === VAULT INDEX ===
   {index content}
   
   === RECENT SPRINTS (last 4) ===
   {sprint contents}
   
   === TEAM PROFILES ===
   {people contents}
   ...
"""
```

---

### `scripts/vault/vault_writer.py`

```python
"""
Functions:

1. write_sprint_file(sprint_id: str, content: str)
   Path: vault/sprints/{YYYY-WW}.md
   
2. write_person_file(name: str, content: str)
   Path: vault/people/{slug}.md (e.g. rob-patrick.md)
   
3. update_index(content: str)
   Path: vault/_index.md
   
4. write_report_archive(report_type: str, content: str)
   Path: vault/reports/{YYYY-MM-DD}-{report_type}.md

5. write_standup_notes(content: str)
   Path: vault/standup-notes/{YYYY-WW}.md

All functions: create parent dirs if missing, overwrite if exists.
"""
```

---

### `scripts/claude_client.py`

```python
"""
Two main calls to implement:

1. compile_vault_updates(raw_data: dict, vault_context: str, cfg: Config) -> VaultUpdates
   
   System prompt: You are a knowledge base compiler for the Kairos engineering team.
   Your job is to update a wiki vault with new information from this week.
   
   User prompt contains:
   - vault_context (existing wiki state)
   - raw_data (all collected data as JSON)
   
   Ask Claude to return JSON with:
   {
     "sprint_file": "...",       # full .md content for this sprint
     "people_updates": {          # partial updates for each person mentioned
       "rob-patrick": "...",
       ...
     },
     "index_update": "...",       # updated _index.md
     "standup_notes": "...",      # digest of standup content
     "new_decisions": [           # any architectural decisions detected
       {"title": "...", "content": "..."}
     ]
   }
   
   Use claude-sonnet-4-20250514, max_tokens=4096, response_format json

2. generate_mindy_report(raw_data: dict, vault_context: str, report_type: str, cfg: Config) -> str
   
   System prompt: You are Mindy, the Kairos team's energetic radio DJ assistant.
   
   User prompt contains all data + vault context.
   
   Returns: the Slack message string (already formatted for Slack)
   
   Slack formatting rules (CRITICAL — embed in prompt):
   - *bold* not **bold**
   - bullet • not - or *
   - no # headers, use --- as section dividers  
   - no :emoji: codes
   - max 2000 chars (signal if needs thread)
   - first names only
   - everyone gets a win
   - end with: {notion_merge_docs_url}
   - gender-neutral references to Mindy
   
   Monday format:
   - Radio DJ energy, celebratory
   - Last week's wins (Done issues grouped by person)
   - What's in flight this week
   - Merge docs link
   
   Friday format:
   - Sprint metrics table (completed / in-progress / QA-ready counts)
   - Completed this week with owner names
   - In Progress
   - Shoutouts
   - Blockers (if any)
   - Merged PRs
   - Merge docs link
"""
```

**Important:** Claude API call should use `anthropic` Python SDK (`pip install anthropic`). For vault compilation, use `response_format` or instruct Claude explicitly to return JSON only.

---

### `scripts/slack_poster.py`

```python
"""
Functions:

1. post_message(channel_id: str, text: str, token: str) -> str (ts of message)
   Uses Slack Web API: POST https://slack.com/api/chat.postMessage
   Headers: Authorization: Bearer {token}
   Body: {"channel": channel_id, "text": text}
   
2. post_thread_reply(channel_id: str, thread_ts: str, text: str, token: str)
   Same API, add "thread_ts": thread_ts to body
   
3. split_and_post(channel_id: str, text: str, token: str)
   If len(text) > 1900: post first 1900 chars as main, rest as thread replies
   Split on newline boundaries, not mid-word.
"""
```

---

### `scripts/orchestrator.py` — main entrypoint

```python
"""
Flow:

1. load_config()
2. Run all collectors in parallel (asyncio or ThreadPoolExecutor):
   - linear_collector.collect()
   - fireflies_collector.collect()
   - github_collector.collect()
   - notion_collector.collect()
   - slack_collector.collect()
3. vault_reader.build_context_bundle() — read existing vault
4. claude_client.compile_vault_updates(raw_data, vault_context, cfg)
5. vault_writer.write_all(vault_updates) — write updated .md files
6. claude_client.generate_mindy_report(raw_data, vault_context, cfg.report_type, cfg)
7. vault_writer.write_report_archive(report_type, mindy_report)
8. If not dry_run:
   - slack_poster.split_and_post(cfg.slack_channel_id, mindy_report, cfg.slack_bot_token)
   - print("Posted to Slack ✓")
9. Print summary of vault files written
"""
```

---

## Vault `.md` file formats

### `vault/_index.md` (maintained by Claude)

```markdown
# Kairos Knowledge Base — Index

*Last updated: YYYY-MM-DD by mindy[bot]*

## Active sprint
- Sprint N (YYYY-MM-DD → YYYY-MM-DD): [[sprints/YYYY-WW]]

## Projects
- [[projects/c1-approximate-schedule]] — Approximate Schedule Intelligence
- [[projects/axon]] — Agent Orchestration Framework
- [[projects/mnemos]] — Memory/RAG Pipeline
- ... (auto-updated)

## Team
- [[people/armando-lopez]] — Head of Agentic Development
- [[people/antwoine-flowers]] — CPTO
- ... (one line per person with role)

## Recent decisions
- YYYY-MM-DD: [[decisions/axon-hybrid-architecture]]
- ...

## Recent standups
- [[standup-notes/YYYY-WW]]
```

### `vault/sprints/YYYY-WW.md`

```markdown
# Sprint N — Week YYYY-WW

*Generated: YYYY-MM-DD*

## Completed
| Issue | Title | Owner | Project |
|-------|-------|-------|---------|
| PDEV-XXX | ... | Rob | C1 |

## In Progress
| Issue | Title | Owner | State |
|-------|-------|-------|-------|

## Ready for Dev

## Merged PRs
- #NNN: title (author)

## Standup highlights
- ...

## Notes
(Claude-generated observations about the sprint)
```

### `vault/people/{slug}.md`

```markdown
# Rob Patrick

*Last updated: YYYY-MM-DD*

## Role
(inferred from Linear activity)

## Recent work
- Sprint N: completed X, Y, Z

## Patterns
(Claude-generated observations about work patterns, areas of focus)

## Backlinks
- [[sprints/YYYY-WW]]
- [[projects/...]]
```

---

## `requirements.txt`

```
anthropic>=0.25.0
requests>=2.31.0
slack-sdk>=3.27.0
PyGithub>=2.3.0
python-dateutil>=2.9.0
```

---

## GitHub Secrets to configure

In the `wvl-kairos-vault` repo settings → Secrets:

| Secret | Value source |
|--------|-------------|
| `ANTHROPIC_API_KEY` | Anthropic console |
| `LINEAR_API_KEY` | Linear Settings → API → Personal API keys |
| `FIREFLIES_API_KEY` | Fireflies Settings → API |
| `SLACK_BOT_TOKEN` | Slack App → OAuth → Bot Token (xoxb-...) |
| `NOTION_TOKEN` | Notion Integrations → Internal integration token |

`GITHUB_TOKEN` is provided automatically by Actions — no secret needed.

---

## Slack app requirements

The Slack bot needs these OAuth scopes:
- `chat:write` — post messages
- `channels:history` — read #meeting-summaries history
- `channels:read` — resolve channel IDs

The bot must be invited to `#meeting-summaries`.

---

## Phased rollout

### Phase 1 — Skeleton (Day 1-2)
- Set up `wvl-kairos-vault` repo
- Implement `config.py` + `orchestrator.py` shell
- Implement `slack_poster.py` (test with a manual message)
- Set up GitHub Actions with `workflow_dispatch` trigger
- Verify secrets load correctly

### Phase 2 — Collectors (Day 2-3)
- Implement `linear_collector.py` — most important source
- Implement `github_collector.py` — PRs are easy
- Implement `fireflies_collector.py`
- Implement `notion_collector.py`
- Run orchestrator locally with `DRY_RUN=true`, print collected data

### Phase 3 — Vault (Day 3-4)
- Implement `vault_reader.py` + `vault_writer.py`
- Seed initial vault with current state (manually write first `_index.md`)
- Implement `claude_client.compile_vault_updates()`
- Test: run full orchestrator in dry run, inspect generated .md files

### Phase 4 — Mindy report (Day 4-5)
- Implement `claude_client.generate_mindy_report()`
- Tune prompts until output matches Mindy format
- End-to-end test with `DRY_RUN=true`, review Slack message in terminal
- First live run on a Monday

### Phase 5 — Hardening
- Add retry logic on API failures (exponential backoff)
- Add Slack notification on workflow failure (post error to #meeting-summaries)
- Add `dry_run` workflow_dispatch option for safe testing
- Monitor first 4 runs manually

---

## Claude prompt design (key constraints)

**Vault compiler system prompt:**
```
You are a knowledge base compiler for the Kairos engineering team at UP Labs.
Your output is always valid JSON. Never add prose outside the JSON object.
You maintain a wiki of .md files following Obsidian conventions:
- Use [[wikilinks]] for cross-references
- Use YAML frontmatter for metadata
- Backlinks are maintained in each file's "Backlinks" section
Your goal: incrementally update the wiki with this week's data, preserving and enriching existing content.
```

**Mindy report system prompt:**
```
You are Mindy, the Kairos team's weekly radio DJ assistant.
Rules: Slack *bold*, bullet •, no # headers, --- dividers, no :emoji: codes, max 2000 chars.
Everyone on the team gets a win. First names only. Gender-neutral.
End every message with the Notion merge docs URL.
Be energetic and celebratory for Monday. Be thorough and data-driven for Friday.
```
