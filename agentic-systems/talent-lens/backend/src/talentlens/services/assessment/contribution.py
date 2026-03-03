"""Individual contribution detection.

Distinguishes between "I built/designed/implemented" (individual) vs
"we built/our team" (collective) statements. Helps assess whether
candidates can articulate their personal impact.
"""


def detect_contributions(transcript: str) -> dict:
    """Analyze transcript for individual vs collective contribution signals.

    Returns:
        {
            "individual_count": int,  # "I built", "I designed", etc.
            "collective_count": int,  # "we built", "our team", etc.
            "ratio": float,           # individual / total
            "examples": [{"text": str, "type": "individual"|"collective"}]
        }
    """
    # TODO: regex + NLP pattern matching for contribution signals
    # TODO: handle LATAM cultural context (may use "we" more modestly)
    raise NotImplementedError
