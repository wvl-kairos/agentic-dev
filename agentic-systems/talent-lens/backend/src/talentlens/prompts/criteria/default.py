"""Default rubric criteria prompt template."""

DEFAULT_CRITERIA_PROMPT = """Evaluate the following criteria for this {interview_type} interview:

{criteria_list}

For each criterion:
1. Find the most relevant quote(s) from the transcript
2. Score from 0 to {max_score}
3. Provide reasoning connecting the evidence to the score

CONTEXT:
- Talk ratio: {talk_ratio:.0%} (candidate speaking time)
- Individual contributions detected: {individual_count}
- Collective references detected: {collective_count}
"""
