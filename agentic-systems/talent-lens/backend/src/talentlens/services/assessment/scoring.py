"""Claude API scoring service.

Sends transcript + rubric criteria to Claude for structured assessment.
Returns scored criteria with evidence quotes and reasoning.
"""

import logging

logger = logging.getLogger(__name__)


async def score_interview(
    transcript: str,
    criteria: list[dict],
    talk_ratio: float,
    contributions: dict,
    interview_type: str,
) -> dict:
    """Score an interview transcript against rubric criteria using Claude.

    Returns:
        {
            "overall_score": float,
            "recommendation": str,
            "summary": str,
            "criteria_scores": [
                {
                    "criterion_name": str,
                    "score": int,
                    "max_score": int,
                    "reasoning": str,
                    "evidence": [{"quote": str, "speaker": str}]
                }
            ]
        }
    """
    # TODO: build prompt from templates
    # TODO: call Claude API with structured output
    # TODO: validate evidence quotes exist in transcript (anti-hallucination)
    raise NotImplementedError
