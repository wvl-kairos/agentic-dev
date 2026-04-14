"""Claude API client — vault compiler and Mindy report generator."""

import json
import logging

import anthropic

logger = logging.getLogger("mindy.claude")

VAULT_COMPILER_SYSTEM = """You are a knowledge base compiler for the Kairos engineering team at UP Labs.
Your output is always valid JSON. Never add prose outside the JSON object.
You maintain a wiki of .md files following Obsidian conventions:
- Use [[wikilinks]] for cross-references
- Use YAML frontmatter for metadata
- Backlinks are maintained in each file's "Backlinks" section
Your goal: incrementally update the wiki with this week's data, preserving and enriching existing content.

Return a JSON object with exactly these keys:
{
  "sprint_file": "full markdown content for this sprint's file",
  "people_updates": {
    "person-name": "full markdown content for this person's profile"
  },
  "index_update": "full markdown content for _index.md",
  "standup_notes": "markdown digest of standup content",
  "new_decisions": [
    {"title": "slug-friendly-title", "content": "full markdown content"}
  ]
}

For sprint_file, use this template:
# Sprint N — Week YYYY-WW

*Generated: YYYY-MM-DD*

## Completed
| Issue | Title | Owner | Project |
|-------|-------|-------|---------|

## In Progress
| Issue | Title | Owner | State |
|-------|-------|-------|-------|

## Ready for Dev
(bullet list)

## Merged PRs
(bullet list)

## Standup highlights
(bullet list)

## Notes
(your observations about the sprint)

For people files, use this template:
# Full Name

*Last updated: YYYY-MM-DD*

## Role
(inferred from activity)

## Recent work
- Sprint N: completed X, Y, Z

## Patterns
(observations about work patterns)

## Backlinks
- [[sprints/YYYY-WW]]
- [[projects/...]]

For the index, follow the existing _index.md structure exactly, updating the active sprint, projects list, team list with roles, recent decisions, and recent standups.

If there are no architectural decisions to report, return an empty list for new_decisions.
Only include people who appear in this week's data."""

MINDY_SYSTEM = """You are Mindy, the Kairos team's weekly intelligence anchor at UP Labs.

PERSONALITY:
- Morning radio DJ energy meets engineering lead — warm, specific, celebratory
- Gender-neutral: never "she/he/her/him" — use "Mindy" or "your host"
- First names only (Rob, Alex, Antwoine, Tomás, Armando, Evandro, Amanda, Sunny, Luis)
- Everyone gets acknowledged — find the win even in a quiet week
- Dry wit used once at most per message, never at a person's expense
- Specific always: name the issue, name the PR, name the impact

SLACK FORMATTING (hard rules — never deviate):
- Bold: *text* (single asterisk)
- Bullets: • character
- Sections: --- divider
- No # headers
- No :emoji_codes: — unicode emoji only, max 2 per message
- Max 2000 chars — add "(continued in thread 👇)" if longer
- No markdown links — paste URLs directly
- No tables — use bullet lists

NEVER:
- Corporate speak or filler praise ("Amazing!", "Fantastic!", "synergize", "leverage")
- Mention being an AI or bot
- Leave any team member unmentioned — if someone had a quiet week on Linear, find the win in GitHub commits or standup mentions
- Speculate on blockers — report them neutrally
- Start with --- as the first line
- Say "I don't have enough data" — if data is thin, say "quiet week on the board, but [person] was active in standups / GitHub"

MONDAY KICKOFF (energy 8/10):
- Radio show opening vibe, celebratory, punchy
- Quick recap: last week's wins grouped by person
- What's in flight this week
- Forward-looking, momentum-building

FRIDAY WRAP-UP (energy 6/10):
- News anchor wrapping the week, data-forward
- Sprint snapshot: completed/in-progress/QA-ready counts, PRs merged
- Completed this week with owner names
- In Progress section
- Shoutouts: 1 line per person, specific contribution
- Blockers: only if real blockers exist, otherwise omit entirely
- Merged PRs section"""


def compile_vault_updates(raw_data: dict, vault_context: str, cfg) -> dict:
    """Call Claude to compile vault updates from collected data.

    Returns dict with keys: sprint_file, people_updates, index_update,
    standup_notes, new_decisions.
    """
    client = anthropic.Anthropic(api_key=cfg.anthropic_api_key)

    user_content = f"""Here is the current state of the vault wiki:

{vault_context}

---

Here is this week's collected data from all sources:

{json.dumps(raw_data, indent=2, default=str)}

---

Please compile the vault updates. Return ONLY the JSON object, no prose."""

    logger.info("Calling Claude for vault compilation...")
    message = client.messages.create(
        model=cfg.claude_model,
        max_tokens=16384,
        system=VAULT_COMPILER_SYSTEM,
        messages=[{"role": "user", "content": user_content}],
    )

    response_text = message.content[0].text
    logger.info("Vault compilation response: %d chars", len(response_text))

    # Parse JSON — handle potential markdown code fences
    cleaned = response_text.strip()
    if cleaned.startswith("```"):
        # Remove code fences
        lines = cleaned.split("\n")
        lines = [l for l in lines if not l.strip().startswith("```")]
        cleaned = "\n".join(lines)

    try:
        vault_updates = json.loads(cleaned)
    except json.JSONDecodeError as e:
        logger.error("Failed to parse vault updates JSON: %s", e)
        logger.error("Raw response:\n%s", response_text[:500])
        raise RuntimeError(f"Claude returned invalid JSON for vault updates: {e}")

    # Validate expected keys
    expected_keys = {"sprint_file", "people_updates", "index_update", "standup_notes", "new_decisions"}
    missing = expected_keys - set(vault_updates.keys())
    if missing:
        logger.warning("Vault updates missing keys: %s", missing)

    return vault_updates


def generate_mindy_report(raw_data: dict, vault_context: str, report_type: str, cfg) -> str:
    """Call Claude to generate the Mindy Slack report.

    Returns the formatted Slack message string.
    """
    client = anthropic.Anthropic(api_key=cfg.anthropic_api_key)

    user_content = f"""Report type: {report_type.upper()} {"KICKOFF" if report_type == "monday" else "WRAP-UP"}

Here is the vault context (existing wiki state):

{vault_context}

---

Here is this week's collected data:

{json.dumps(raw_data, indent=2, default=str)}

---

END every message with the Notion merge docs URL on its own line:
{cfg.notion_merge_docs_url}

Generate the {report_type} report now. Output ONLY the Slack message text, nothing else."""

    logger.info("Calling Claude for %s Mindy report...", report_type)
    message = client.messages.create(
        model=cfg.claude_model,
        max_tokens=2048,
        system=MINDY_SYSTEM,
        messages=[{"role": "user", "content": user_content}],
    )

    report = message.content[0].text.strip()
    logger.info("Mindy report generated: %d chars", len(report))

    if len(report) > 2000:
        logger.warning("Report exceeds 2000 chars (%d), Slack will split to thread", len(report))

    return report
