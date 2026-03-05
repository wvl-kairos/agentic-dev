"""Generate structured job descriptions from role templates using Claude API."""

import json
import logging

import anthropic

from talentlens.config import settings

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a senior technical recruiter writing job descriptions for a technology venture studio (UP Labs).

RULES:
- Write professional, compelling job descriptions that attract top engineering talent
- Use the capability requirements and technology stack to define what the role needs
- Proficiency levels 1-5 map to: 1=Beginner, 2=Junior, 3=Mid-level, 4=Senior, 5=Expert
- Only list technologies and capabilities that are explicitly provided — do not invent requirements
- Be specific about what the candidate will work on based on the role description
- Use inclusive language
- Keep sections concise and scannable

You MUST respond with valid JSON only, no markdown formatting."""

USER_PROMPT_TEMPLATE = """Generate a job description for the following role template.

## Role
- Title: {name}
- Description: {description}

## Required Capabilities (General Engineering Skills)
{capabilities_block}

## Required Technology Stack
{technologies_block}

## Required JSON Output
{{
  "title": "<job title>",
  "summary": "<2-3 sentence role summary>",
  "about_role": "<1-2 paragraph description of what the person will do>",
  "responsibilities": ["<responsibility 1>", "<responsibility 2>", ...],
  "required_qualifications": ["<qualification 1>", "<qualification 2>", ...],
  "preferred_qualifications": ["<nice-to-have 1>", ...],
  "tech_stack": ["<technology 1>", "<technology 2>", ...],
  "level": "<Junior|Mid-level|Senior|Staff|Principal based on overall capability requirements>"
}}"""

LEVEL_LABELS = {1: "Beginner", 2: "Junior", 3: "Mid-level", 4: "Senior", 5: "Expert"}


def _build_capabilities_block(capabilities: list[dict]) -> str:
    if not capabilities:
        return "No specific capability requirements defined."
    lines = []
    for cap in capabilities:
        level = cap.get("required_level", 3)
        label = LEVEL_LABELS.get(level, f"Level {level}")
        lines.append(f"- {cap['name']}: {label} (level {level}/5)")
        if cap.get("description"):
            lines.append(f"  {cap['description']}")
    return "\n".join(lines)


def _build_technologies_block(technologies: list[dict]) -> str:
    if not technologies:
        return "No specific technology requirements defined."
    lines = []
    for tech in technologies:
        level = tech.get("required_level", 3)
        label = LEVEL_LABELS.get(level, f"Level {level}")
        cap_name = tech.get("capability_name", "")
        prefix = f"[{cap_name}] " if cap_name else ""
        lines.append(f"- {prefix}{tech['name']}: {label} (level {level}/5)")
    return "\n".join(lines)


async def generate_job_description(
    name: str,
    description: str | None,
    capabilities: list[dict],
    technologies: list[dict],
) -> dict:
    """Generate a structured job description from role template data.

    Args:
        name: Role template name
        description: Role template description
        capabilities: List of {name, description, required_level}
        technologies: List of {name, capability_name, required_level}

    Returns:
        Structured job description dict
    """
    if not settings.anthropic_api_key:
        logger.error("No Anthropic API key configured")
        return {
            "title": name,
            "summary": "Job description generation unavailable: API key not configured.",
            "about_role": "",
            "responsibilities": [],
            "required_qualifications": [],
            "preferred_qualifications": [],
            "tech_stack": [],
            "level": "Mid-level",
        }

    capabilities_block = _build_capabilities_block(capabilities)
    technologies_block = _build_technologies_block(technologies)

    user_prompt = USER_PROMPT_TEMPLATE.format(
        name=name,
        description=description or "No description provided.",
        capabilities_block=capabilities_block,
        technologies_block=technologies_block,
    )

    client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)

    message = await client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=2048,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_prompt}],
    )

    response_text = message.content[0].text
    try:
        result = json.loads(response_text)
    except json.JSONDecodeError:
        logger.error("Claude returned invalid JSON for JD: %.200s", response_text)
        return {
            "title": name,
            "summary": "Failed to generate job description.",
            "about_role": response_text,
            "responsibilities": [],
            "required_qualifications": [],
            "preferred_qualifications": [],
            "tech_stack": [],
            "level": "Mid-level",
        }

    logger.info("Generated JD for role template: %s → %s", name, result.get("title"))
    return result
