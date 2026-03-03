"""Claude API scoring service.

Sends transcript + rubric criteria to Claude for structured assessment.
Returns scored criteria with evidence quotes and reasoning.
Validates that evidence quotes actually exist in the transcript (anti-hallucination).
"""

import json
import logging

import anthropic

from talentlens.config import settings

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are an expert interview assessor for a technology venture studio (UP Labs).
Your role is to evaluate candidate interviews based on specific rubric criteria.

RULES:
- Score ONLY based on evidence from the transcript
- Every score MUST be supported by a direct quote from the transcript
- Quotes must be EXACT substrings from the transcript — do not paraphrase
- If a criterion cannot be evaluated from the transcript, score it as 0 with reasoning "Not enough evidence in transcript"
- Be culturally sensitive: LATAM candidates may use "we" modestly even for individual work
- Distinguish between genuine team references and cultural humility
- Consider talk ratio and contribution patterns as additional signals, not primary scoring factors

You MUST respond with valid JSON only, no markdown formatting."""

USER_PROMPT_TEMPLATE = """Evaluate this {interview_type} interview transcript against the rubric criteria below.

## Pre-computed Metrics
- Talk ratio: {talk_ratio:.0%} (candidate speaking time)
- Individual contribution statements: {individual_count}
- Collective contribution statements: {collective_count}
- Contribution ratio: {contribution_ratio:.0%} individual

## Rubric Criteria
{criteria_block}

## Transcript
{transcript}

## Required JSON Output
{{
  "overall_score": <weighted average 0.0-5.0>,
  "recommendation": "<strong_yes|yes|lean_yes|lean_no|no|strong_no>",
  "summary": "<2-3 sentence assessment>",
  "criteria_scores": [
    {{
      "criterion_name": "<exact criterion name>",
      "score": <0-max_score>,
      "max_score": <from rubric>,
      "reasoning": "<why this score>",
      "evidence": [
        {{"quote": "<exact substring from transcript>", "speaker": "<speaker name>"}}
      ]
    }}
  ]
}}"""


def _build_criteria_block(criteria: list[dict]) -> str:
    lines = []
    for i, c in enumerate(criteria, 1):
        name = c.get("name", f"Criterion {i}")
        desc = c.get("description", "")
        weight = c.get("weight", 1.0)
        max_score = c.get("max_score", 5)
        lines.append(f"{i}. **{name}** (weight: {weight}, max: {max_score})")
        if desc:
            lines.append(f"   {desc}")
    return "\n".join(lines)


def _validate_evidence(result: dict, transcript: str) -> dict:
    """Validate that evidence quotes exist in the transcript. Remove hallucinated quotes."""
    transcript_lower = transcript.lower()
    for cs in result.get("criteria_scores", []):
        valid_evidence = []
        for ev in cs.get("evidence", []):
            quote = ev.get("quote", "")
            if quote.lower() in transcript_lower:
                valid_evidence.append(ev)
            else:
                logger.warning(
                    "Removed hallucinated quote for %s: %.80s...",
                    cs.get("criterion_name"),
                    quote,
                )
        cs["evidence"] = valid_evidence
    return result


async def score_interview(
    transcript: str,
    criteria: list[dict],
    talk_ratio: float,
    contributions: dict,
    interview_type: str,
) -> dict:
    """Score an interview transcript against rubric criteria using Claude.

    Returns structured assessment with scores, reasoning, and validated evidence.
    """
    if not settings.anthropic_api_key:
        logger.error("No Anthropic API key configured")
        return {
            "overall_score": 0,
            "recommendation": "no",
            "summary": "Assessment unavailable: Anthropic API key not configured.",
            "criteria_scores": [],
        }

    # Build the prompt
    criteria_block = _build_criteria_block(criteria)
    user_prompt = USER_PROMPT_TEMPLATE.format(
        interview_type=interview_type,
        talk_ratio=talk_ratio,
        individual_count=contributions.get("individual_count", 0),
        collective_count=contributions.get("collective_count", 0),
        contribution_ratio=contributions.get("ratio", 0),
        criteria_block=criteria_block,
        transcript=transcript,
    )

    # Call Claude
    client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)

    message = await client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=4096,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_prompt}],
    )

    # Parse response
    response_text = message.content[0].text
    try:
        result = json.loads(response_text)
    except json.JSONDecodeError:
        logger.error("Claude returned invalid JSON: %.200s", response_text)
        return {
            "overall_score": 0,
            "recommendation": "no",
            "summary": f"Assessment failed: could not parse Claude response.",
            "criteria_scores": [],
            "raw_response": response_text,
        }

    # Validate evidence quotes against transcript
    result = _validate_evidence(result, transcript)

    # Attach raw response for audit
    result["raw_response"] = response_text

    logger.info(
        "Scored interview: %.1f/5.0 → %s",
        result.get("overall_score", 0),
        result.get("recommendation", "unknown"),
    )
    return result
