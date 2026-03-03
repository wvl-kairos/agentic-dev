"""Talk ratio analysis prompt."""

TALK_RATIO_PROMPT = """Analyze the talk ratio in this interview:

Candidate talk time: {talk_ratio:.0%}
Interview type: {interview_type}

Interpret the talk ratio:
- Screening: candidate should speak 60-80% of the time
- Technical: candidate should speak 50-70% (more back-and-forth expected)
- Final: depends on format, typically 50-60%

Provide a brief assessment of what the talk ratio suggests about the interview dynamics.
"""
