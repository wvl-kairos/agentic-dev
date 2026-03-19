"""Generate AI-powered interview guides from role templates using Claude API."""

import json
import logging

import anthropic

from talentlens.config import settings
from talentlens.services.job_description import (
    _build_capabilities_block,
    _build_technologies_block,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Stage configuration
# ---------------------------------------------------------------------------

STAGE_CONTEXT: dict[str, dict] = {
    "initial": {
        "name": "Initial Interview",
        "depth": "high-level",
        "focus": "motivation, culture fit, communication style",
        "question_count": 5,
        "description": (
            "First conversation with the candidate. Assess motivation for the role, "
            "alignment with company culture, communication skills, and career trajectory."
        ),
    },
    "screening": {
        "name": "Screening",
        "depth": "moderate",
        "focus": "breadth of technical knowledge, problem-solving approach",
        "question_count": 6,
        "description": (
            "Technical breadth assessment. Evaluate the candidate's range of knowledge "
            "across the required stack, ability to articulate tradeoffs, and practical experience."
        ),
    },
    "coderpad": {
        "name": "CoderPad",
        "depth": "hands-on coding",
        "focus": "live coding, implementation, debugging",
        "question_count": 3,
        "description": (
            "Live coding session (20-30 minutes each). Problems should test real-world "
            "implementation skills, not algorithmic puzzles. Evaluate code quality, "
            "testing instincts, and thought process."
        ),
    },
    "technical": {
        "name": "Technical Deep-Dive",
        "depth": "deep",
        "focus": "system design, architecture, scalability",
        "question_count": 5,
        "description": (
            "Senior-level technical interview. Assess system design ability, architectural "
            "thinking, scalability awareness, and depth in core technologies."
        ),
    },
    "final": {
        "name": "Final Interview",
        "depth": "strategic",
        "focus": "leadership, vision, team dynamics",
        "question_count": 5,
        "description": (
            "Leadership and culture conversation. Evaluate strategic thinking, team "
            "collaboration, conflict resolution, and long-term vision alignment."
        ),
    },
}

SYSTEM_PROMPT = """You are an expert technical interviewer designing compound interview questions for a technology venture studio (UP Labs).

RULES:
- Each question MUST be a compound scenario that evaluates 2-4 technologies or capabilities simultaneously
- Calibrate difficulty to the proficiency levels provided (1=Beginner, 2=Junior, 3=Mid-level, 4=Senior, 5=Expert)
- Technologies marked as "Required" (must_have) should receive heavier coverage across questions
- Questions should feel like real work scenarios, not textbook problems
- Include concrete context (e.g., "Your team just deployed..." or "A client reports...")
- Follow-up probes should dig deeper into specific technologies mentioned in the main question
- "what_good_looks_like" should describe observable behaviors, not just correct answers
- Difficulty must be one of: "easy", "medium", "hard"
- Distribute difficulty across questions appropriately for the interview stage

You MUST respond with valid JSON only, no markdown formatting."""

USER_PROMPT_TEMPLATE = """Generate an interview guide for the following role and stage.

## Role
- Title: {name}
- Description: {description}

## Interview Stage
- Stage: {stage_name}
- Depth: {depth}
- Focus: {focus}
- Context: {stage_description}
- Number of questions: {question_count}

## Required Capabilities (General Engineering Skills)
{capabilities_block}

## Required Technology Stack
{technologies_block}

## Required JSON Output
{{
  "questions": [
    {{
      "number": 1,
      "question": "<compound scenario question evaluating 2-4 technologies>",
      "evaluates": {{
        "capabilities": ["<capability name 1>", "<capability name 2>"],
        "technologies": ["<tech 1>", "<tech 2>"]
      }},
      "difficulty": "easy|medium|hard",
      "expected_duration_minutes": <number>,
      "what_good_looks_like": "<description of a strong answer>",
      "follow_ups": [
        {{
          "probe": "<follow-up question>",
          "targets": "<what this probes for>"
        }}
      ]
    }}
  ],
  "interviewer_tips": [
    "<practical tip for conducting this interview stage>"
  ]
}}"""


async def generate_interview_guide(
    role_name: str,
    role_description: str | None,
    stage: str,
    capabilities: list[dict],
    technologies: list[dict],
) -> dict:
    """Generate an interview guide from role template data.

    Args:
        role_name: Role template name
        role_description: Role template description
        stage: Interview stage key (initial, screening, coderpad, technical, final)
        capabilities: List of {name, description, required_level}
        technologies: List of {name, capability_name, required_level, priority}

    Returns:
        Structured interview guide dict
    """
    stage_ctx = STAGE_CONTEXT.get(stage)
    if not stage_ctx:
        return _fallback_response(role_name, stage, "Invalid stage")

    if not settings.anthropic_api_key:
        logger.error("No Anthropic API key configured")
        return _fallback_response(role_name, stage, "API key not configured")

    capabilities_block = _build_capabilities_block(capabilities)
    technologies_block = _build_technologies_block(technologies)

    user_prompt = USER_PROMPT_TEMPLATE.format(
        name=role_name,
        description=role_description or "No description provided.",
        stage_name=stage_ctx["name"],
        depth=stage_ctx["depth"],
        focus=stage_ctx["focus"],
        stage_description=stage_ctx["description"],
        question_count=stage_ctx["question_count"],
        capabilities_block=capabilities_block,
        technologies_block=technologies_block,
    )

    client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)

    message = await client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=4096,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_prompt}],
    )

    response_text = message.content[0].text

    # Strip markdown code fences if Claude wraps the JSON
    cleaned = response_text.strip()
    if cleaned.startswith("```"):
        first_newline = cleaned.index("\n") if "\n" in cleaned else len(cleaned)
        cleaned = cleaned[first_newline + 1 :]
        if cleaned.rstrip().endswith("```"):
            cleaned = cleaned.rstrip()[:-3].rstrip()

    try:
        result = json.loads(cleaned)
    except json.JSONDecodeError:
        logger.error("Claude returned invalid JSON for interview guide: %.200s", response_text)
        return _fallback_response(role_name, stage, "Failed to parse AI response")

    # Compute estimated total duration
    questions = result.get("questions", [])
    total_minutes = sum(q.get("expected_duration_minutes", 10) for q in questions)

    logger.info("Generated interview guide for %s / %s (%d questions)", role_name, stage, len(questions))
    return {
        "stage": stage,
        "stage_name": stage_ctx["name"],
        "role_name": role_name,
        "estimated_duration_minutes": total_minutes,
        "questions": questions,
        "interviewer_tips": result.get("interviewer_tips", []),
    }


def _fallback_response(role_name: str, stage: str, reason: str) -> dict:
    """Return a safe fallback when generation fails."""
    stage_ctx = STAGE_CONTEXT.get(stage, STAGE_CONTEXT["screening"])
    return {
        "stage": stage,
        "stage_name": stage_ctx["name"],
        "role_name": role_name,
        "estimated_duration_minutes": 0,
        "questions": [],
        "interviewer_tips": [f"Interview guide generation unavailable: {reason}"],
    }
