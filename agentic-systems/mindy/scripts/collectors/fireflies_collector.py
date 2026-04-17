"""Fireflies collector — fetches standup transcripts via GraphQL API."""

import json
import logging
from datetime import datetime, timedelta, timezone

import anthropic
from retry import retry_request

logger = logging.getLogger("mindy.collectors.fireflies")

FIREFLIES_API = "https://api.fireflies.ai/graphql"
REQUEST_TIMEOUT = 30

# --- Sensitivity filtering constants ---

MIN_PARTICIPANTS = 3  # Layer 1: skip 1:1s and solo recordings

SENSITIVE_TITLE_KEYWORDS = [
    "1:1", "one-on-one", "1-on-1", "one on one",
    "performance", "review", "feedback",
    "compensation", "salary", "termination",
    "pip", "probation", "confidential",
    "hr", "disciplinary", "exit interview",
]

SENSITIVITY_MODEL = "claude-haiku-4-5-20251001"

SENSITIVITY_SYSTEM_PROMPT = """\
You are a sensitivity classifier for meeting transcripts.
Classify whether a meeting is sensitive and should NOT appear in a public Slack report.

SENSITIVE (exclude) — meetings about:
- HR topics, performance reviews, PIPs, disciplinary actions
- Personal issues, health, family matters
- Salary, compensation, equity, bonuses
- Legal matters, contracts, NDAs
- 1:1 manager/report conversations
- Hiring decisions about specific candidates
- Terminations, layoffs, restructuring

NOT SENSITIVE (include) — meetings about:
- Standups, sprint planning, retrospectives
- Technical design, architecture discussions
- Product roadmap, feature planning
- Team-wide announcements
- Bug triage, incident reviews
- Cross-team syncs, demos

Respond with ONLY valid JSON: {"sensitive": true/false, "reason": "brief reason"}
"""


def _query(api_key: str, query: str, variables: dict = None) -> dict:
    """Execute a Fireflies GraphQL query with retry."""
    resp = retry_request(
        "POST", FIREFLIES_API,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json={"query": query, "variables": variables or {}},
        timeout=REQUEST_TIMEOUT,
    )
    resp.raise_for_status()
    data = resp.json()
    if "errors" in data:
        raise RuntimeError(f"Fireflies GraphQL errors: {data['errors']}")
    return data.get("data", {})


def _get_transcripts(api_key: str, organizer_email: str, since: datetime) -> list:
    """Get standup transcripts from the past week."""
    result = _query(api_key, """
        query($fromDate: DateTime, $toDate: DateTime) {
            transcripts(fromDate: $fromDate, toDate: $toDate) {
                id
                title
                date
                organizer_email
                participants
                summary {
                    action_items
                    overview
                    shorthand_bullet
                }
            }
        }
    """, {
        "fromDate": since.isoformat(),
        "toDate": datetime.now(timezone.utc).isoformat(),
    })

    transcripts = result.get("transcripts") or []

    # Filter by organizer
    filtered = [
        t for t in transcripts
        if (t.get("organizer_email") or "").lower() == organizer_email.lower()
    ]

    logger.info(
        "Fireflies transcripts: %d total, %d from %s",
        len(transcripts), len(filtered), organizer_email,
    )

    return [
        {
            "id": t["id"],
            "title": t.get("title", ""),
            "date": t.get("date", ""),
            "participants": t.get("participants") or [],
            "action_items": (t.get("summary") or {}).get("action_items") or [],
            "overview": (t.get("summary") or {}).get("overview", ""),
            "bullets": (t.get("summary") or {}).get("shorthand_bullet") or [],
        }
        for t in filtered
    ]


def _has_enough_participants(transcript: dict) -> bool:
    """Layer 1: Skip meetings with fewer than MIN_PARTICIPANTS."""
    return len(transcript.get("participants") or []) >= MIN_PARTICIPANTS


def _has_sensitive_title(title: str) -> bool:
    """Layer 2: Check if title contains sensitive keywords."""
    lower = title.lower()
    return any(kw in lower for kw in SENSITIVE_TITLE_KEYWORDS)


def _llm_sensitivity_check(api_key: str, title: str, overview: str) -> bool:
    """Layer 3: Ask Haiku whether the meeting is sensitive.

    Returns True if the meeting is sensitive (should be excluded).
    Fail-safe: returns True (exclude) on any error.
    """
    try:
        client = anthropic.Anthropic(api_key=api_key)
        message = client.messages.create(
            model=SENSITIVITY_MODEL,
            max_tokens=150,
            system=SENSITIVITY_SYSTEM_PROMPT,
            messages=[{
                "role": "user",
                "content": f"Meeting title: {title}\nOverview: {overview}",
            }],
        )
        raw = message.content[0].text.strip()
        result = json.loads(raw)
        return result["sensitive"]
    except Exception as exc:
        logger.warning("LLM sensitivity check failed for '%s': %s — excluding", title, exc)
        return True  # fail-safe: exclude on error


def _is_safe_for_sharing(transcript: dict, api_key: str) -> bool:
    """Run all 3 sensitivity layers. Returns True if transcript is safe to share."""
    title = transcript.get("title", "")

    # Layer 1: participant count
    if not _has_enough_participants(transcript):
        logger.debug("Filtered (participants < %d): %s", MIN_PARTICIPANTS, title)
        return False

    # Layer 2: title keywords
    if _has_sensitive_title(title):
        logger.debug("Filtered (sensitive title): %s", title)
        return False

    # Layer 3: LLM check
    overview = transcript.get("overview", "")
    if _llm_sensitivity_check(api_key, title, overview):
        logger.debug("Filtered (LLM flagged sensitive): %s", title)
        return False

    return True


def collect(cfg) -> dict:
    """Collect standup data from Fireflies."""
    since = datetime.now(timezone.utc) - timedelta(days=7)
    standups = _get_transcripts(cfg.fireflies_api_key, cfg.fireflies_organizer, since)

    before = len(standups)
    standups = [s for s in standups if _is_safe_for_sharing(s, cfg.anthropic_api_key)]
    logger.info(
        "Sensitivity filter: %d → %d transcripts (%d excluded)",
        before, len(standups), before - len(standups),
    )

    return {"standups": standups}
