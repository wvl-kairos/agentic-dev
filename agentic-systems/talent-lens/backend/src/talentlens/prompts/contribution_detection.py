"""Contribution detection prompt."""

CONTRIBUTION_DETECTION_PROMPT = """Analyze the candidate's statements for individual vs collective contributions.

Individual indicators: "I built", "I designed", "I led", "I implemented", "my approach"
Collective indicators: "we built", "our team", "we decided", "the team"

IMPORTANT: LATAM candidates may use collective language out of cultural humility,
not because they lack individual ownership. Look for follow-up specifics that
indicate personal contribution even when framed collectively.

Transcript excerpt:
{transcript_excerpt}

Classify each contribution statement and assess the candidate's ability
to articulate their personal impact.
"""
